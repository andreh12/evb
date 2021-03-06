#ifndef _evb_Constants_h_
#define _evb_Constants_h_

#include <algorithm>
#include <arpa/inet.h>
#include <iomanip>
#include <iterator>
#include <netdb.h>
#include <sstream>
#include <stdint.h>
#include <string.h>
#include <time.h>


namespace evb {

  const uint16_t GTPe_FED_ID         =     814; //0x32e
  const uint16_t TCDS_FED_ID         =    1024;
  const uint16_t SOFT_FED_ID         =    1022;
  const uint32_t ORBITS_PER_LS       = 0x40000; //2^18 orbits
  const uint16_t FED_COUNT           =    4096;
  const uint16_t FEROL_BLOCK_SIZE    =    4096;
  const uint16_t LOWEST_PRIORITY     =       6; //Priorities go from 0 to LOWEST_PRIORITY

  static const uint64_t fibonacci[] = {1ULL,2ULL,3ULL,5ULL,8ULL,13ULL,21ULL,34ULL,55ULL,89ULL,144ULL,233ULL,377ULL,610ULL,987ULL,1597ULL,2584ULL,4181ULL,6765ULL,10946ULL,17711ULL,28657ULL,46368ULL,75025ULL,121393ULL,196418ULL,317811ULL,514229ULL,832040ULL,1346269ULL,2178309ULL,3524578ULL,5702887ULL,9227465ULL,14930352ULL,24157817ULL,39088169ULL,63245986ULL,102334155ULL,165580141ULL,267914296ULL,433494437ULL,701408733ULL,1134903170ULL,1836311903ULL,2971215073ULL,4807526976ULL,7778742049ULL,12586269025ULL,20365011074ULL,32951280099ULL,53316291173ULL,86267571272ULL,139583862445ULL,225851433717ULL,365435296162ULL,591286729879ULL,956722026041ULL,1548008755920ULL,2504730781961ULL,4052739537881ULL,6557470319842ULL,10610209857723ULL,17167680177565ULL,27777890035288ULL,44945570212853ULL,72723460248141ULL,117669030460994ULL,190392490709135ULL,308061521170129ULL,498454011879264ULL,806515533049393ULL,1304969544928657ULL,2111485077978050ULL,3416454622906707ULL,5527939700884757ULL,8944394323791464ULL,14472334024676221ULL,23416728348467685ULL,37889062373143906ULL,61305790721611591ULL,99194853094755497ULL,160500643816367088ULL,259695496911122585ULL,420196140727489673ULL,679891637638612258ULL,1100087778366101931ULL,1779979416004714189ULL,2880067194370816120ULL,4660046610375530309ULL,7540113804746346429ULL,12200160415121876738ULL};

  inline bool isFibonacci(const uint64_t value)
  { return ( std::find(fibonacci,fibonacci+92,value) != fibonacci+92 ); }

  inline uint64_t getTimeStamp()
  {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (ts.tv_sec*1000000000 + ts.tv_nsec);
  }

  inline std::string doubleToString(const double& value, const uint8_t precision)
  {
    std::ostringstream str;
    str.setf(std::ios::fixed);
    str.precision(precision);
    str << value;
    return str.str();
  }

  inline std::string resolveIPaddress(const std::string& hostname)
  {
    struct addrinfo hints,*addr;
    char ipstr[INET6_ADDRSTRLEN];

    memset(&hints,0,sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_DGRAM;

    const int errcode = getaddrinfo(hostname.c_str(), "", &hints, &addr);
    if (errcode)
    {
      throw gai_strerror(errcode);
    }

    if (addr->ai_family == AF_INET)
    {
      inet_ntop(AF_INET,
                &((struct sockaddr_in*)addr->ai_addr)->sin_addr,
                ipstr, sizeof(ipstr));
    }
    else // AF_INET6
    {
      inet_ntop(AF_INET6,
                &((struct sockaddr_in6*)addr->ai_addr)->sin6_addr,
                ipstr, sizeof(ipstr));
    }
    return ipstr;
  }

} // namespace evb

#endif


/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
