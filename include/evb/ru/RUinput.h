#ifndef _evb_ru_RUinput_h_
#define _evb_ru_RUinput_h_

#include <boost/scoped_ptr.hpp>
#include <boost/thread/mutex.hpp>

#include <map>
#include <stdint.h>

#include "log4cplus/logger.h"

#include "evb/EvBid.h"
#include "evb/EvBidFactory.h"
#include "evb/FragmentChain.h"
#include "evb/FragmentTracker.h"
#include "evb/InfoSpaceItems.h"
#include "evb/readoutunit/Configuration.h"
#include "evb/readoutunit/Input.h"
#include "pt/utcp/frl/MemoryCache.h"
#include "toolbox/mem/Pool.h"
#include "toolbox/mem/Reference.h"
#include "xdaq/Application.h"
#include "xdata/Boolean.h"
#include "xdata/String.h"
#include "xdata/UnsignedInteger32.h"
#include "xdata/UnsignedInteger64.h"
#include "xdata/Vector.h"
#include "xgi/Output.h"


namespace evb {

  class RU;
  
  namespace ru {
    
    /**
     * \ingroup xdaqApps
     * \brief Event fragment input handler of RU
     */
    
    class RUinput : public readoutunit::Input<readoutunit::Configuration>
    {

    public:
      
      RUinput
      (
        xdaq::ApplicationStub* app,
        boost::shared_ptr<readoutunit::Configuration> configuration
      ) :
      readoutunit::Input<readoutunit::Configuration>(app,configuration) {};
      
    private:
      
      class FEROLproxy : public readoutunit::Input<readoutunit::Configuration>::FEROLproxy
      {
      public:
        
        virtual bool getSuperFragmentWithEvBid(const EvBid&, FragmentChainPtr&);
      };
      
      class DummyInputData : public readoutunit::Input<readoutunit::Configuration>::DummyInputData
      {
      public:
        
        DummyInputData(RUinput* input)
        : readoutunit::Input<readoutunit::Configuration>::DummyInputData(input) {};
        
        virtual bool getSuperFragmentWithEvBid(const EvBid& evbId, FragmentChainPtr& superFragment)
        { return createSuperFragment(evbId,superFragment); }
        
      };
      
      virtual void getHandlerForInputSource(boost::shared_ptr<Handler>& handler)
      {
        const std::string inputSource = configuration_->inputSource.toString();
        
        if ( inputSource == "FEROL" )
        {
          handler.reset( new FEROLproxy() );
        }
        else if ( inputSource == "Local" )
        {
          handler.reset( new DummyInputData(this) );
        }
        else
        {
          XCEPT_RAISE(exception::Configuration,
            "Unknown input source " + inputSource + " requested.");
        }
      }
      
    };
    
    
  } } //namespace evb::ru


#endif // _evb_ru_RUinput_h_

/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -