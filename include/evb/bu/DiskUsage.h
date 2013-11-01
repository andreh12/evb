#ifndef _evb_bu_DiskUsage_h_
#define _evb_bu_DiskUsage_h_

#include <boost/filesystem/convenience.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/thread/mutex.hpp>

#include <stdint.h>
#include <sys/statfs.h>


namespace evb {
  namespace bu {

    /**
     * \ingroup xdaqApps
     * \brief Monitor disk usage
     */

    class DiskUsage
    {
    public:

      DiskUsage
      (
        const boost::filesystem::path& path,
        const float lowWaterMark,
        const float highWaterMark,
        const bool deleteFiles
      );

      ~DiskUsage();

      /**
       * Update the information about the disk
       * Returns false if the disk cannot be accesssed
       */
      bool update();

      /**
       * Returns the change in the relative disk usage
       * btw the low and high water mark.
       */
      float overThreshold();

      /**
       * Return the disk size in GB
       */
      float diskSizeGB();

      /**
       * Return the relative usage of the disk in percent
       */
      float relDiskUsage();


    private:

      void doStatFs();

      const boost::filesystem::path path_;
      const float lowWaterMark_;
      const float highWaterMark_;
      const bool deleteFiles_;

      boost::mutex mutex_;
      int retVal_;
      struct statfs64 statfs_;
    };

    typedef boost::shared_ptr<DiskUsage> DiskUsagePtr;

  } } // namespace evb::bu

#endif // _evb_bu_DiskUsage_h_


/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
