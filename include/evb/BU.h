#ifndef _evb_bu_h_
#define _evb_bu_h_

#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>

#include <string>

#include "evb/EvBApplication.h"
#include "evb/PerformanceMonitor.h"
#include "evb/bu/StateMachine.h"
#include "toolbox/mem/Reference.h"
#include "toolbox/task/WorkLoop.h"
#include "xdaq/ApplicationStub.h"
#include "xdata/Double.h"
#include "xdata/UnsignedInteger32.h"
#include "xdata/UnsignedInteger64.h"
#include "xgi/Output.h"


namespace evb {
  
  class InfoSpaceItems;
  class TimerManager;
  
  namespace bu {
    class RUproxy;
    class EventTable;
  }

  /**
   * \ingroup xdaqApps
   * \brief Builder Unit (BU)
   */
  
  class BU : public EvBApplication<bu::StateMachine>
  {
    
  public:

    BU(xdaq::ApplicationStub*);

    virtual ~BU() {};
       
    XDAQ_INSTANTIATOR();
   
    /**
     * Configure
     */
    void configure();

    /**
     * Remove all data
     */
    void clear();
    
    
  private:
    
    virtual void bindI2oCallbacks();
    inline void I2O_BU_CACHE_Callback(toolbox::mem::Reference*);
    
    virtual void do_appendApplicationInfoSpaceItems(InfoSpaceItems&);
    virtual void do_appendMonitoringInfoSpaceItems(InfoSpaceItems&);
    virtual void do_updateMonitoringInfo();
    
    virtual void do_handleItemRetrieveEvent(const std::string& item);
  
    virtual void bindNonDefaultXgiCallbacks();
    virtual void do_defaultWebPage(xgi::Output*);
    void printHtml(xgi::Output*);
    
    void fragmentFIFOWebPage(xgi::Input*, xgi::Output*);
    void blockFIFOWebPage(xgi::Input*, xgi::Output*);
    void eventFIFOWebPage(xgi::Input*, xgi::Output*);
    void eolsFIFOWebPage(xgi::Input*, xgi::Output*);
    
    boost::shared_ptr<bu::DiskWriter> diskWriter_;
    boost::shared_ptr<bu::EventTable> eventTable_;
    boost::shared_ptr<bu::RUproxy> ruProxy_;
    
    xdata::UnsignedInteger32 nbEvtsUnderConstruction_;
    xdata::UnsignedInteger32 nbEventsInBU_;
    xdata::UnsignedInteger32 nbEvtsReady_;
    xdata::UnsignedInteger32 nbEvtsBuilt_;
    xdata::UnsignedInteger32 nbEvtsCorrupted_;
    xdata::UnsignedInteger32 nbFilesWritten_;
  };
  
  
} //namespace evb

#endif // _evb_bu_h_

/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
