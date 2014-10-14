#include <sstream>
#include <string>

#include <boost/lexical_cast.hpp>

#include "evb/BU.h"
#include "evb/bu/DiskWriter.h"
#include "evb/bu/EventBuilder.h"
#include "evb/bu/ResourceManager.h"
#include "evb/bu/StateMachine.h"
#include "evb/Exception.h"
#include "toolbox/task/WorkLoopFactory.h"
#include "xcept/tools.h"


evb::bu::EventBuilder::EventBuilder
(
  BU* bu,
  boost::shared_ptr<DiskWriter> diskWriter,
  boost::shared_ptr<ResourceManager> resourceManager
) :
  bu_(bu),
  diskWriter_(diskWriter),
  resourceManager_(resourceManager),
  configuration_(bu->getConfiguration()),
  corruptedEvents_(0),
  eventsWithCRCerrors_(0),
  doProcessing_(false),
  writeNextEventsToFile_(0)
{
  builderAction_ =
    toolbox::task::bind(this, &evb::bu::EventBuilder::process,
                        bu_->getIdentifier("eventBuilder") );
}


void evb::bu::EventBuilder::addSuperFragment
(
  const uint16_t builderId,
  FragmentChainPtr& superFragments
)
{
  superFragmentFIFOs_[builderId]->enqWait(superFragments);
}


void evb::bu::EventBuilder::configure()
{
  superFragmentFIFOs_.clear();
  writeNextEventsToFile_ = 0;

  processesActive_.clear();
  processesActive_.resize(configuration_->numberOfBuilders.value_);

  for (uint16_t i=0; i < configuration_->numberOfBuilders; ++i)
  {
    std::ostringstream fifoName;
    fifoName << "superFragmentFIFO_" << i;
    SuperFragmentFIFOPtr superFragmentFIFO( new SuperFragmentFIFO(bu_,fifoName.str()) );
    superFragmentFIFO->resize(configuration_->superFragmentFIFOCapacity);
    superFragmentFIFOs_.insert( SuperFragmentFIFOs::value_type(i,superFragmentFIFO) );

    eventMapMonitors_.insert( EventMapMonitors::value_type(i,EventMapMonitor()) );
  }

  createProcessingWorkLoops();
}


void evb::bu::EventBuilder::createProcessingWorkLoops()
{
  const std::string identifier = bu_->getIdentifier();

  try
  {
    // Leave any previous created workloops alone. Only add new ones if needed.
    for (uint16_t i=builderWorkLoops_.size(); i < configuration_->numberOfBuilders; ++i)
    {
      std::ostringstream workLoopName;
      workLoopName << identifier << "/Builder_" << i;
      toolbox::task::WorkLoop* wl = toolbox::task::getWorkLoopFactory()->getWorkLoop( workLoopName.str(), "waiting" );

      if ( ! wl->isActive() ) wl->activate();
      builderWorkLoops_.push_back(wl);
    }
  }
  catch(xcept::Exception& e)
  {
    XCEPT_RETHROW(exception::WorkLoop, "Failed to start workloops", e);
  }
}


void evb::bu::EventBuilder::startProcessing(const uint32_t runNumber)
{
  runNumber_ = runNumber;
  corruptedEvents_ = 0;
  eventsWithCRCerrors_ = 0;
  doProcessing_ = true;
  for (uint32_t i=0; i < configuration_->numberOfBuilders; ++i)
  {
    builderWorkLoops_.at(i)->submit(builderAction_);
  }
}


void evb::bu::EventBuilder::drain()
{
  while ( processesActive_.any() ) ::usleep(1000);
}


void evb::bu::EventBuilder::stopProcessing()
{
  doProcessing_ = false;

  drain();

  for (SuperFragmentFIFOs::const_iterator it = superFragmentFIFOs_.begin(), itEnd = superFragmentFIFOs_.end();
       it != itEnd; ++it)
  {
    it->second->clear();
  }
}


bool evb::bu::EventBuilder::process(toolbox::task::WorkLoop* wl)
{
  const std::string wlName =  wl->getName();
  const size_t startPos = wlName.find_last_of("_") + 1;
  const size_t endPos = wlName.find("/",startPos);
  const uint16_t builderId = boost::lexical_cast<uint16_t>( wlName.substr(startPos,endPos-startPos) );

  {
    boost::mutex::scoped_lock sl(processesActiveMutex_);
    processesActive_.set(builderId);
  }

  FragmentChainPtr superFragments;
  SuperFragmentFIFOPtr superFragmentFIFO = superFragmentFIFOs_[builderId];

  PartialEvents partialEvents;
  CompleteEvents completeEvents;
  EventMapMonitor& eventMapMonitor = eventMapMonitors_[builderId];

  StreamHandlerPtr streamHandler;
  if ( ! configuration_->dropEventData )
    streamHandler = diskWriter_->getStreamHandler(builderId);

  try
  {
    while ( doProcessing_ )
    {
      bool workDone = false;

      if ( superFragmentFIFO->deq(superFragments) )
      {
        buildEvent(superFragments,partialEvents,completeEvents);
        eventMapMonitor.partialEvents = partialEvents.size();
        workDone = true;
      }

      if ( ! completeEvents.empty() )
      {
        workDone = true;
        try
        {
          eventMapMonitor.lowestLumiSection = completeEvents.begin()->first;
          handleCompleteEvents(completeEvents,streamHandler);
          eventMapMonitor.completeEvents = completeEvents.size();
        }
        catch(exception::DataCorruption& e)
        {
          ++corruptedEvents_;

          LOG4CPLUS_ERROR(bu_->getApplicationLogger(),
                          xcept::stdformat_exception_history(e));
          bu_->notifyQualified("error",e);
        }
        catch(exception::CRCerror& e)
        {
          ++eventsWithCRCerrors_;

          if ( evb::isFibonacci(eventsWithCRCerrors_) )
          {
            std::ostringstream msg;
            msg << "received " << eventsWithCRCerrors_ << " events with CRC error";

            XCEPT_DECLARE_NESTED(exception::CRCerror,sentinelError,msg.str(),e);
            bu_->notifyQualified("error",sentinelError);

            msg << ": " << xcept::stdformat_exception_history(e);
            LOG4CPLUS_ERROR(bu_->getApplicationLogger(),msg.str());
          }
        }
      }

      if ( ! workDone )
      {
        boost::mutex::scoped_lock sl(processesActiveMutex_);
        processesActive_.reset(builderId);
        sl.unlock();
        ::usleep(1000);
        sl.lock();
        processesActive_.set(builderId);
      }
    }
  }
  catch(xcept::Exception& e)
  {
    {
      boost::mutex::scoped_lock sl(processesActiveMutex_);
      processesActive_.reset(builderId);
    }
    stateMachine_->processFSMEvent( Fail(e) );
  }
  catch(std::exception& e)
  {
    {
      boost::mutex::scoped_lock sl(processesActiveMutex_);
      processesActive_.reset(builderId);
    }
    XCEPT_DECLARE(exception::SuperFragment,
                  sentinelException, e.what());
    stateMachine_->processFSMEvent( Fail(sentinelException) );
  }
  catch(...)
  {
    {
      boost::mutex::scoped_lock sl(processesActiveMutex_);
      processesActive_.reset(builderId);
    }
    XCEPT_DECLARE(exception::SuperFragment,
                  sentinelException, "unkown exception");
    stateMachine_->processFSMEvent( Fail(sentinelException) );
  }

  {
    boost::mutex::scoped_lock sl(processesActiveMutex_);
    processesActive_.reset(builderId);
  }

  return false;
}


inline void evb::bu::EventBuilder::buildEvent
(
  FragmentChainPtr& superFragments,
  PartialEvents& partialEvents,
  CompleteEvents& completeEvents
) const
{
  toolbox::mem::Reference* bufRef = superFragments->head()->duplicate();
  const I2O_MESSAGE_FRAME* stdMsg =
    (I2O_MESSAGE_FRAME*)bufRef->getDataLocation();
  const msg::I2O_DATA_BLOCK_MESSAGE_FRAME* dataBlockMsg =
    (msg::I2O_DATA_BLOCK_MESSAGE_FRAME*)stdMsg;
  const I2O_TID ruTid = stdMsg->InitiatorAddress;
  const uint16_t nbSuperFragments = dataBlockMsg->nbSuperFragments;
  uint16_t superFragmentCount = 0;
  const uint32_t blockHeaderSize = dataBlockMsg->getHeaderSize();

  PartialEvents::iterator eventPos = getEventPos(partialEvents,dataBlockMsg,superFragmentCount);

  do
  {
    toolbox::mem::Reference* nextRef = bufRef->getNextReference();
    bufRef->setNextReference(0);

    unsigned char* payload = (unsigned char*)bufRef->getDataLocation() + blockHeaderSize;
    uint32_t remainingBufferSize = bufRef->getDataSize() - blockHeaderSize;

    while ( remainingBufferSize > 0 && nbSuperFragments != superFragmentCount )
    {
      const msg::SuperFragment* superFragmentMsg = (msg::SuperFragment*)payload;
      const uint32_t headerSize = superFragmentMsg->getHeaderSize();

      if ( eventPos->second->appendSuperFragment(ruTid,
                                                 bufRef->duplicate(),
                                                 payload) )
      {
        // the super fragment is complete
        if ( eventPos->second->isComplete() )
        {
          // the event is complete, too
          const uint32_t lumiSection = eventPos->first.lumiSection();
          completeEvents.insert(CompleteEvents::value_type(lumiSection,eventPos->second));
          partialEvents.erase(eventPos);
        }

        ++superFragmentCount;
        eventPos = getEventPos(partialEvents,dataBlockMsg,superFragmentCount);
      }

      const uint32_t size = headerSize + superFragmentMsg->partSize;
      payload += size;
      remainingBufferSize -= size;
      if ( remainingBufferSize < sizeof(msg::SuperFragment) )
        remainingBufferSize = 0;
    }

    bufRef->release();
    bufRef = nextRef;

  } while ( bufRef );

  if (superFragmentCount != nbSuperFragments)
  {
    std::ostringstream oss;
    oss << "Incomplete I2O_DATA_BLOCK_MESSAGE_FRAME from RU TID " << ruTid;
    oss << ": expected " << nbSuperFragments << " super fragments, but found " << superFragmentCount;
    XCEPT_RAISE(exception::SuperFragment, oss.str());
  }
}


inline evb::bu::EventBuilder::PartialEvents::iterator evb::bu::EventBuilder::getEventPos
(
  PartialEvents& partialEvents,
  const msg::I2O_DATA_BLOCK_MESSAGE_FRAME*& dataBlockMsg,
  const uint16_t& superFragmentCount
) const
{
  if ( superFragmentCount >= dataBlockMsg->nbSuperFragments )
    return partialEvents.end();

  const EvBid evbId = dataBlockMsg->evbIds[superFragmentCount];

  PartialEvents::iterator eventPos = partialEvents.lower_bound(evbId);
  if ( eventPos == partialEvents.end() || (partialEvents.key_comp()(evbId,eventPos->first)) )
  {
    // new event
    EventPtr event( new Event(evbId, dataBlockMsg) );
    eventPos = partialEvents.insert(eventPos, PartialEvents::value_type(evbId,event));
  }
  return eventPos;
}


void evb::bu::EventBuilder::handleCompleteEvents
(
  CompleteEvents& completeEvents,
  StreamHandlerPtr& streamHandler
) const
{
  const uint32_t oldestIncompleteLumiSection = resourceManager_->getOldestIncompleteLumiSection();

  CompleteEvents::iterator pos = completeEvents.begin();

  while ( pos != completeEvents.end() && pos->first == oldestIncompleteLumiSection )
  {
    const EventPtr& event = pos->second;

    resourceManager_->eventCompleted(event);

    try
    {
      event->checkEvent(configuration_->checkCRC);
    }
    catch(exception::DataCorruption& e)
    {
      resourceManager_->discardEvent(event);
      completeEvents.erase(pos++);
      throw; // rethrow the exception such that it can be handled outside of critical section
    }
    catch(exception::CRCerror& e)
    {
      if ( ! configuration_->dropEventData )
        streamHandler->writeEvent(event);

      resourceManager_->discardEvent(event);
      completeEvents.erase(pos++);
      throw; // rethrow the exception such that it can be handled outside of critical section
    }

    if ( writeNextEventsToFile_ > 0 )
    {
      boost::mutex::scoped_lock sl(writeNextEventsToFileMutex_);
      if ( writeNextEventsToFile_ > 0 ) // recheck once we have the lock
      {
        event->dumpEventToFile("Requested by user");
        --writeNextEventsToFile_;
      }
    }

    if ( ! configuration_->dropEventData )
      streamHandler->writeEvent(event);

    resourceManager_->discardEvent(event);
    completeEvents.erase(pos++);
  }
}


void evb::bu::EventBuilder::appendMonitoringItems(InfoSpaceItems& items)
{
  nbCorruptedEvents_ = 0;
  nbEventsWithCRCerrors_ = 0;

  items.add("nbCorruptedEvents", &nbCorruptedEvents_);
  items.add("nbEventsWithCRCerrors", &nbEventsWithCRCerrors_);
}


void evb::bu::EventBuilder::updateMonitoringItems()
{
  nbCorruptedEvents_ = corruptedEvents_;
  nbEventsWithCRCerrors_ = eventsWithCRCerrors_;
}


void evb::bu::EventBuilder::writeNextEventsToFile(const uint16_t count)
{
  boost::mutex::scoped_lock sl(writeNextEventsToFileMutex_);
  writeNextEventsToFile_ = count;
}


cgicc::div evb::bu::EventBuilder::getHtmlSnipped() const
{
  using namespace cgicc;

  cgicc::div div;
  div.add(p("EventBuilder"));

  {
    cgicc::table table;
    table.set("title","Number of bad events since the beginning of the run.");

    table.add(tr()
              .add(td("# corrupted events"))
              .add(td(boost::lexical_cast<std::string>(corruptedEvents_))));
    table.add(tr()
              .add(td("# events w/ CRC errors"))
              .add(td(boost::lexical_cast<std::string>(eventsWithCRCerrors_))));

    div.add(table);
  }

  {
    cgicc::table table;
    table.set("title","List of builder threads. Each thread assembles events independently. Any complete event is held back until all threads have reached the next lumi section.");

    boost::mutex::scoped_lock sl(processesActiveMutex_);

    table.add(tr()
              .add(th("Event builders").set("colspan","5")));
    table.add(tr()
              .add(td("builder"))
              .add(td("active"))
              .add(td("ls"))
              .add(td("#partial"))
              .add(td("#complete")));

    for ( EventMapMonitors::const_iterator it = eventMapMonitors_.begin(), itEnd = eventMapMonitors_.end();
          it != itEnd; ++it )
    {
      table.add(tr()
                .add(td(boost::lexical_cast<std::string>(it->first)))
                .add(td(processesActive_[it->first]?"yes":"no"))
                .add(td(boost::lexical_cast<std::string>(it->second.lowestLumiSection)))
                .add(td(boost::lexical_cast<std::string>(it->second.partialEvents)))
                .add(td(boost::lexical_cast<std::string>(it->second.completeEvents))));
    }

    div.add(table);
  }

  if ( ! superFragmentFIFOs_.empty() )
  {
    cgicc::div fifos;
    fifos.set("title","FIFOs holding super-fragments to be fed to the corresponding builder threads.");

    SuperFragmentFIFOs::const_iterator it = superFragmentFIFOs_.begin();
    while ( it != superFragmentFIFOs_.end() )
    {
      try
      {
        fifos.add(it->second->getHtmlSnipped());
        ++it;
      }
      catch(...) {}
    }

    div.add(fifos);
  }

  div.add(br());
  const std::string javaScript = "function dumpEvents(count) { var options = { url:'/" +
    bu_->getURN().toString() + "/writeNextEventsToFile?count='+count }; xdaqAJAX(options,null); }";
  div.add(script(javaScript).set("type","text/javascript"));
  div.add(button("dump next event").set("type","button").set("title","dump the next event to /tmp")
          .set("onclick","dumpEvents(1);"));

  return div;
}


/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
