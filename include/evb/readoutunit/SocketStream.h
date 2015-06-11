#ifndef _evb_readoutunit_SocketStream_h_
#define _evb_readoutunit_SocketStream_h_

#include <stdint.h>
#include <string.h>

#include "evb/OneToOneQueue.h"
#include "evb/readoutunit/Configuration.h"
#include "evb/readoutunit/FerolStream.h"
#include "evb/readoutunit/ReadoutUnit.h"
#include "evb/readoutunit/SocketBuffer.h"
#include "evb/readoutunit/StateMachine.h"
#include "interface/shared/ferol_header.h"
#include "pt/blit/InputPipe.h"
#include "toolbox/lang/Class.h"
#include "toolbox/mem/Reference.h"
#include "toolbox/task/Action.h"
#include "toolbox/task/WaitingWorkLoop.h"
#include "toolbox/task/WorkLoopFactory.h"
#include "xcept/tools.h"


namespace evb {

  namespace readoutunit {

   /**
    * \ingroup xdaqApps
    * \brief Represent a stream of locally generated FEROL data
    */

    template<class ReadoutUnit, class Configuration>
    class SocketStream : public FerolStream<ReadoutUnit,Configuration>, public toolbox::lang::Class
    {
    public:

      SocketStream(ReadoutUnit*, const typename Configuration::FerolSource*);

      /**
       * Handle the next buffer from pt::blit
       */
      void addBuffer(toolbox::mem::Reference*, pt::blit::InputPipe*);

      /**
       * Configure
       */
      void configure();

      /**
       * Start processing events
       */
      virtual void startProcessing(const uint32_t runNumber);

      /**
       * Drain the remainig events
       */
      virtual void drain();

      /**
       * Stop processing events
       */
      virtual void stopProcessing();

      /**
       * Return the information about the FEROL connected to this stream
       */
      const typename Configuration::FerolSource* getFerolSource() const
      { return ferolSource_; }


    private:
      void startProcessingWorkLoop();
      bool process(toolbox::task::WorkLoop*);

      const typename Configuration::FerolSource* ferolSource_;

      typedef OneToOneQueue<SocketBufferPtr> SocketBufferFIFO;
      SocketBufferFIFO socketBufferFIFO_;

      toolbox::task::WorkLoop* processingWorkLoop_;
      toolbox::task::ActionSignature* processingAction_;

      volatile bool processingActive_;

      FedFragmentPtr currentFragment_;

    };

  } } // namespace evb::readoutunit


////////////////////////////////////////////////////////////////////////////////
// Implementation follows                                                     //
////////////////////////////////////////////////////////////////////////////////

template<class ReadoutUnit,class Configuration>
evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::SocketStream
(
  ReadoutUnit* readoutUnit,
  const typename Configuration::FerolSource* ferolSource
) :
  FerolStream<ReadoutUnit,Configuration>(readoutUnit,ferolSource->fedId.value_),
  ferolSource_(ferolSource),
  socketBufferFIFO_(readoutUnit,"socketBufferFIFO"),
  processingActive_(false)
{
  startProcessingWorkLoop();
}



template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::startProcessingWorkLoop()
{
  try
  {
    processingWorkLoop_ = toolbox::task::getWorkLoopFactory()->
      getWorkLoop( this->readoutUnit_->getIdentifier("socketStream"), "waiting" );

    if ( ! processingWorkLoop_->isActive() )
    {
      processingAction_ =
        toolbox::task::bind(this, &evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::process,
                            this->readoutUnit_->getIdentifier("processSocketBuffers") );

      processingWorkLoop_->activate();
    }
  }
  catch(xcept::Exception& e)
  {
    std::string msg = "Failed to start workloop 'socketStream'";
    XCEPT_RETHROW(exception::WorkLoop, msg, e);
  }
}


template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::addBuffer(toolbox::mem::Reference* bufRef, pt::blit::InputPipe* inputPipe)
{
  SocketBufferPtr socketBuffer( new SocketBuffer(bufRef,inputPipe) );

  if ( this->doProcessing_ )
    socketBufferFIFO_.enqWait(socketBuffer);

  // if we are not processing, we just drop the data to the floor
  // SocketBuffer takes care of freeing the resources
}


template<class ReadoutUnit,class Configuration>
bool evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::process(toolbox::task::WorkLoop* wl)
{
  if ( ! this->doProcessing_ ) return false;

  SocketBufferPtr socketBuffer;
  while ( socketBufferFIFO_.deq(socketBuffer) )
  {
    const uint32_t bufSize = socketBuffer->getBufRef()->getDataSize();
    uint32_t usedSize = 0;

    while ( usedSize < bufSize )
    {
      if ( ! currentFragment_ )
        currentFragment_ = this->fedFragmentFactory_.getFedFragment();

      this->fedFragmentFactory_.append(currentFragment_,socketBuffer,usedSize);

      if ( currentFragment_->isComplete() )
      {
        this->addFedFragment(currentFragment_);
        currentFragment_.reset();
      }
    }
  }

  ::usleep(10);

  return this->doProcessing_;
}


template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::configure()
{
  socketBufferFIFO_.resize(this->readoutUnit_->getConfiguration()->socketBufferFIFOCapacity);
}


template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::startProcessing(const uint32_t runNumber)
{
  FerolStream<ReadoutUnit,Configuration>::startProcessing(runNumber);
  processingWorkLoop_->submit(processingAction_);
}


template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::drain()
{
  while ( processingActive_ || !socketBufferFIFO_.empty() ) ::sleep(1000);
  FerolStream<ReadoutUnit,Configuration>::drain();
}


template<class ReadoutUnit,class Configuration>
void evb::readoutunit::SocketStream<ReadoutUnit,Configuration>::stopProcessing()
{
  FerolStream<ReadoutUnit,Configuration>::stopProcessing();
  socketBufferFIFO_.clear();
}


#endif // _evb_readoutunit_SocketStream_h_


/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
