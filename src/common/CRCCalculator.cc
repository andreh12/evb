#include "evb/CRCCalculator.h"

const uint16_t evb::crcTable[1024] = {
  0x0000, 0x8005, 0x800f, 0x000a, 0x801b, 0x001e, 0x0014, 0x8011,
  0x8033, 0x0036, 0x003c, 0x8039, 0x0028, 0x802d, 0x8027, 0x0022,
  0x8063, 0x0066, 0x006c, 0x8069, 0x0078, 0x807d, 0x8077, 0x0072,
  0x0050, 0x8055, 0x805f, 0x005a, 0x804b, 0x004e, 0x0044, 0x8041,
  0x80c3, 0x00c6, 0x00cc, 0x80c9, 0x00d8, 0x80dd, 0x80d7, 0x00d2,
  0x00f0, 0x80f5, 0x80ff, 0x00fa, 0x80eb, 0x00ee, 0x00e4, 0x80e1,
  0x00a0, 0x80a5, 0x80af, 0x00aa, 0x80bb, 0x00be, 0x00b4, 0x80b1,
  0x8093, 0x0096, 0x009c, 0x8099, 0x0088, 0x808d, 0x8087, 0x0082,
  0x8183, 0x0186, 0x018c, 0x8189, 0x0198, 0x819d, 0x8197, 0x0192,
  0x01b0, 0x81b5, 0x81bf, 0x01ba, 0x81ab, 0x01ae, 0x01a4, 0x81a1,
  0x01e0, 0x81e5, 0x81ef, 0x01ea, 0x81fb, 0x01fe, 0x01f4, 0x81f1,
  0x81d3, 0x01d6, 0x01dc, 0x81d9, 0x01c8, 0x81cd, 0x81c7, 0x01c2,
  0x0140, 0x8145, 0x814f, 0x014a, 0x815b, 0x015e, 0x0154, 0x8151,
  0x8173, 0x0176, 0x017c, 0x8179, 0x0168, 0x816d, 0x8167, 0x0162,
  0x8123, 0x0126, 0x012c, 0x8129, 0x0138, 0x813d, 0x8137, 0x0132,
  0x0110, 0x8115, 0x811f, 0x011a, 0x810b, 0x010e, 0x0104, 0x8101,
  0x8303, 0x0306, 0x030c, 0x8309, 0x0318, 0x831d, 0x8317, 0x0312,
  0x0330, 0x8335, 0x833f, 0x033a, 0x832b, 0x032e, 0x0324, 0x8321,
  0x0360, 0x8365, 0x836f, 0x036a, 0x837b, 0x037e, 0x0374, 0x8371,
  0x8353, 0x0356, 0x035c, 0x8359, 0x0348, 0x834d, 0x8347, 0x0342,
  0x03c0, 0x83c5, 0x83cf, 0x03ca, 0x83db, 0x03de, 0x03d4, 0x83d1,
  0x83f3, 0x03f6, 0x03fc, 0x83f9, 0x03e8, 0x83ed, 0x83e7, 0x03e2,
  0x83a3, 0x03a6, 0x03ac, 0x83a9, 0x03b8, 0x83bd, 0x83b7, 0x03b2,
  0x0390, 0x8395, 0x839f, 0x039a, 0x838b, 0x038e, 0x0384, 0x8381,
  0x0280, 0x8285, 0x828f, 0x028a, 0x829b, 0x029e, 0x0294, 0x8291,
  0x82b3, 0x02b6, 0x02bc, 0x82b9, 0x02a8, 0x82ad, 0x82a7, 0x02a2,
  0x82e3, 0x02e6, 0x02ec, 0x82e9, 0x02f8, 0x82fd, 0x82f7, 0x02f2,
  0x02d0, 0x82d5, 0x82df, 0x02da, 0x82cb, 0x02ce, 0x02c4, 0x82c1,
  0x8243, 0x0246, 0x024c, 0x8249, 0x0258, 0x825d, 0x8257, 0x0252,
  0x0270, 0x8275, 0x827f, 0x027a, 0x826b, 0x026e, 0x0264, 0x8261,
  0x0220, 0x8225, 0x822f, 0x022a, 0x823b, 0x023e, 0x0234, 0x8231,
  0x8213, 0x0216, 0x021c, 0x8219, 0x0208, 0x820d, 0x8207, 0x0202,
  0x0000, 0x8603, 0x8c03, 0x0a00, 0x9803, 0x1e00, 0x1400, 0x9203,
  0xb003, 0x3600, 0x3c00, 0xba03, 0x2800, 0xae03, 0xa403, 0x2200,
  0xe003, 0x6600, 0x6c00, 0xea03, 0x7800, 0xfe03, 0xf403, 0x7200,
  0x5000, 0xd603, 0xdc03, 0x5a00, 0xc803, 0x4e00, 0x4400, 0xc203,
  0x4003, 0xc600, 0xcc00, 0x4a03, 0xd800, 0x5e03, 0x5403, 0xd200,
  0xf000, 0x7603, 0x7c03, 0xfa00, 0x6803, 0xee00, 0xe400, 0x6203,
  0xa000, 0x2603, 0x2c03, 0xaa00, 0x3803, 0xbe00, 0xb400, 0x3203,
  0x1003, 0x9600, 0x9c00, 0x1a03, 0x8800, 0x0e03, 0x0403, 0x8200,
  0x8006, 0x0605, 0x0c05, 0x8a06, 0x1805, 0x9e06, 0x9406, 0x1205,
  0x3005, 0xb606, 0xbc06, 0x3a05, 0xa806, 0x2e05, 0x2405, 0xa206,
  0x6005, 0xe606, 0xec06, 0x6a05, 0xf806, 0x7e05, 0x7405, 0xf206,
  0xd006, 0x5605, 0x5c05, 0xda06, 0x4805, 0xce06, 0xc406, 0x4205,
  0xc005, 0x4606, 0x4c06, 0xca05, 0x5806, 0xde05, 0xd405, 0x5206,
  0x7006, 0xf605, 0xfc05, 0x7a06, 0xe805, 0x6e06, 0x6406, 0xe205,
  0x2006, 0xa605, 0xac05, 0x2a06, 0xb805, 0x3e06, 0x3406, 0xb205,
  0x9005, 0x1606, 0x1c06, 0x9a05, 0x0806, 0x8e05, 0x8405, 0x0206,
  0x8009, 0x060a, 0x0c0a, 0x8a09, 0x180a, 0x9e09, 0x9409, 0x120a,
  0x300a, 0xb609, 0xbc09, 0x3a0a, 0xa809, 0x2e0a, 0x240a, 0xa209,
  0x600a, 0xe609, 0xec09, 0x6a0a, 0xf809, 0x7e0a, 0x740a, 0xf209,
  0xd009, 0x560a, 0x5c0a, 0xda09, 0x480a, 0xce09, 0xc409, 0x420a,
  0xc00a, 0x4609, 0x4c09, 0xca0a, 0x5809, 0xde0a, 0xd40a, 0x5209,
  0x7009, 0xf60a, 0xfc0a, 0x7a09, 0xe80a, 0x6e09, 0x6409, 0xe20a,
  0x2009, 0xa60a, 0xac0a, 0x2a09, 0xb80a, 0x3e09, 0x3409, 0xb20a,
  0x900a, 0x1609, 0x1c09, 0x9a0a, 0x0809, 0x8e0a, 0x840a, 0x0209,
  0x000f, 0x860c, 0x8c0c, 0x0a0f, 0x980c, 0x1e0f, 0x140f, 0x920c,
  0xb00c, 0x360f, 0x3c0f, 0xba0c, 0x280f, 0xae0c, 0xa40c, 0x220f,
  0xe00c, 0x660f, 0x6c0f, 0xea0c, 0x780f, 0xfe0c, 0xf40c, 0x720f,
  0x500f, 0xd60c, 0xdc0c, 0x5a0f, 0xc80c, 0x4e0f, 0x440f, 0xc20c,
  0x400c, 0xc60f, 0xcc0f, 0x4a0c, 0xd80f, 0x5e0c, 0x540c, 0xd20f,
  0xf00f, 0x760c, 0x7c0c, 0xfa0f, 0x680c, 0xee0f, 0xe40f, 0x620c,
  0xa00f, 0x260c, 0x2c0c, 0xaa0f, 0x380c, 0xbe0f, 0xb40f, 0x320c,
  0x100c, 0x960f, 0x9c0f, 0x1a0c, 0x880f, 0x0e0c, 0x040c, 0x820f,
  0x0000, 0x8017, 0x802b, 0x003c, 0x8053, 0x0044, 0x0078, 0x806f,
  0x80a3, 0x00b4, 0x0088, 0x809f, 0x00f0, 0x80e7, 0x80db, 0x00cc,
  0x8143, 0x0154, 0x0168, 0x817f, 0x0110, 0x8107, 0x813b, 0x012c,
  0x01e0, 0x81f7, 0x81cb, 0x01dc, 0x81b3, 0x01a4, 0x0198, 0x818f,
  0x8283, 0x0294, 0x02a8, 0x82bf, 0x02d0, 0x82c7, 0x82fb, 0x02ec,
  0x0220, 0x8237, 0x820b, 0x021c, 0x8273, 0x0264, 0x0258, 0x824f,
  0x03c0, 0x83d7, 0x83eb, 0x03fc, 0x8393, 0x0384, 0x03b8, 0x83af,
  0x8363, 0x0374, 0x0348, 0x835f, 0x0330, 0x8327, 0x831b, 0x030c,
  0x8503, 0x0514, 0x0528, 0x853f, 0x0550, 0x8547, 0x857b, 0x056c,
  0x05a0, 0x85b7, 0x858b, 0x059c, 0x85f3, 0x05e4, 0x05d8, 0x85cf,
  0x0440, 0x8457, 0x846b, 0x047c, 0x8413, 0x0404, 0x0438, 0x842f,
  0x84e3, 0x04f4, 0x04c8, 0x84df, 0x04b0, 0x84a7, 0x849b, 0x048c,
  0x0780, 0x8797, 0x87ab, 0x07bc, 0x87d3, 0x07c4, 0x07f8, 0x87ef,
  0x8723, 0x0734, 0x0708, 0x871f, 0x0770, 0x8767, 0x875b, 0x074c,
  0x86c3, 0x06d4, 0x06e8, 0x86ff, 0x0690, 0x8687, 0x86bb, 0x06ac,
  0x0660, 0x8677, 0x864b, 0x065c, 0x8633, 0x0624, 0x0618, 0x860f,
  0x8a03, 0x0a14, 0x0a28, 0x8a3f, 0x0a50, 0x8a47, 0x8a7b, 0x0a6c,
  0x0aa0, 0x8ab7, 0x8a8b, 0x0a9c, 0x8af3, 0x0ae4, 0x0ad8, 0x8acf,
  0x0b40, 0x8b57, 0x8b6b, 0x0b7c, 0x8b13, 0x0b04, 0x0b38, 0x8b2f,
  0x8be3, 0x0bf4, 0x0bc8, 0x8bdf, 0x0bb0, 0x8ba7, 0x8b9b, 0x0b8c,
  0x0880, 0x8897, 0x88ab, 0x08bc, 0x88d3, 0x08c4, 0x08f8, 0x88ef,
  0x8823, 0x0834, 0x0808, 0x881f, 0x0870, 0x8867, 0x885b, 0x084c,
  0x89c3, 0x09d4, 0x09e8, 0x89ff, 0x0990, 0x8987, 0x89bb, 0x09ac,
  0x0960, 0x8977, 0x894b, 0x095c, 0x8933, 0x0924, 0x0918, 0x890f,
  0x0f00, 0x8f17, 0x8f2b, 0x0f3c, 0x8f53, 0x0f44, 0x0f78, 0x8f6f,
  0x8fa3, 0x0fb4, 0x0f88, 0x8f9f, 0x0ff0, 0x8fe7, 0x8fdb, 0x0fcc,
  0x8e43, 0x0e54, 0x0e68, 0x8e7f, 0x0e10, 0x8e07, 0x8e3b, 0x0e2c,
  0x0ee0, 0x8ef7, 0x8ecb, 0x0edc, 0x8eb3, 0x0ea4, 0x0e98, 0x8e8f,
  0x8d83, 0x0d94, 0x0da8, 0x8dbf, 0x0dd0, 0x8dc7, 0x8dfb, 0x0dec,
  0x0d20, 0x8d37, 0x8d0b, 0x0d1c, 0x8d73, 0x0d64, 0x0d58, 0x8d4f,
  0x0cc0, 0x8cd7, 0x8ceb, 0x0cfc, 0x8c93, 0x0c84, 0x0cb8, 0x8caf,
  0x8c63, 0x0c74, 0x0c48, 0x8c5f, 0x0c30, 0x8c27, 0x8c1b, 0x0c0c,
  0x0000, 0x9403, 0xa803, 0x3c00, 0xd003, 0x4400, 0x7800, 0xec03,
  0x2003, 0xb400, 0x8800, 0x1c03, 0xf000, 0x6403, 0x5803, 0xcc00,
  0x4006, 0xd405, 0xe805, 0x7c06, 0x9005, 0x0406, 0x3806, 0xac05,
  0x6005, 0xf406, 0xc806, 0x5c05, 0xb006, 0x2405, 0x1805, 0x8c06,
  0x800c, 0x140f, 0x280f, 0xbc0c, 0x500f, 0xc40c, 0xf80c, 0x6c0f,
  0xa00f, 0x340c, 0x080c, 0x9c0f, 0x700c, 0xe40f, 0xd80f, 0x4c0c,
  0xc00a, 0x5409, 0x6809, 0xfc0a, 0x1009, 0x840a, 0xb80a, 0x2c09,
  0xe009, 0x740a, 0x480a, 0xdc09, 0x300a, 0xa409, 0x9809, 0x0c0a,
  0x801d, 0x141e, 0x281e, 0xbc1d, 0x501e, 0xc41d, 0xf81d, 0x6c1e,
  0xa01e, 0x341d, 0x081d, 0x9c1e, 0x701d, 0xe41e, 0xd81e, 0x4c1d,
  0xc01b, 0x5418, 0x6818, 0xfc1b, 0x1018, 0x841b, 0xb81b, 0x2c18,
  0xe018, 0x741b, 0x481b, 0xdc18, 0x301b, 0xa418, 0x9818, 0x0c1b,
  0x0011, 0x9412, 0xa812, 0x3c11, 0xd012, 0x4411, 0x7811, 0xec12,
  0x2012, 0xb411, 0x8811, 0x1c12, 0xf011, 0x6412, 0x5812, 0xcc11,
  0x4017, 0xd414, 0xe814, 0x7c17, 0x9014, 0x0417, 0x3817, 0xac14,
  0x6014, 0xf417, 0xc817, 0x5c14, 0xb017, 0x2414, 0x1814, 0x8c17,
  0x803f, 0x143c, 0x283c, 0xbc3f, 0x503c, 0xc43f, 0xf83f, 0x6c3c,
  0xa03c, 0x343f, 0x083f, 0x9c3c, 0x703f, 0xe43c, 0xd83c, 0x4c3f,
  0xc039, 0x543a, 0x683a, 0xfc39, 0x103a, 0x8439, 0xb839, 0x2c3a,
  0xe03a, 0x7439, 0x4839, 0xdc3a, 0x3039, 0xa43a, 0x983a, 0x0c39,
  0x0033, 0x9430, 0xa830, 0x3c33, 0xd030, 0x4433, 0x7833, 0xec30,
  0x2030, 0xb433, 0x8833, 0x1c30, 0xf033, 0x6430, 0x5830, 0xcc33,
  0x4035, 0xd436, 0xe836, 0x7c35, 0x9036, 0x0435, 0x3835, 0xac36,
  0x6036, 0xf435, 0xc835, 0x5c36, 0xb035, 0x2436, 0x1836, 0x8c35,
  0x0022, 0x9421, 0xa821, 0x3c22, 0xd021, 0x4422, 0x7822, 0xec21,
  0x2021, 0xb422, 0x8822, 0x1c21, 0xf022, 0x6421, 0x5821, 0xcc22,
  0x4024, 0xd427, 0xe827, 0x7c24, 0x9027, 0x0424, 0x3824, 0xac27,
  0x6027, 0xf424, 0xc824, 0x5c27, 0xb024, 0x2427, 0x1827, 0x8c24,
  0x802e, 0x142d, 0x282d, 0xbc2e, 0x502d, 0xc42e, 0xf82e, 0x6c2d,
  0xa02d, 0x342e, 0x082e, 0x9c2d, 0x702e, 0xe42d, 0xd82d, 0x4c2e,
  0xc028, 0x542b, 0x682b, 0xfc28, 0x102b, 0x8428, 0xb828, 0x2c2b,
  0xe02b, 0x7428, 0x4828, 0xdc2b, 0x3028, 0xa42b, 0x982b, 0x0c28
};

// Check if the CPU supports PCLMULQDQ
// see e.g. http://stackoverflow.com/a/6491964/288875 or the Linux kernel
// see http://en.wikipedia.org/wiki/CPUID#EAX.3D1:_Processor_Info_and_Feature_Bits
// for the meaning of the bits
static inline bool hasPCLMULQDQ()
{
  unsigned int ebx(0), ecx(0), edx(0);
  unsigned int eax(1); // we want processor info and feature bits

  // ecx is often an input as well as an output.
  asm volatile("cpuid"
               : "=a" (eax),
                 "=b" (ebx),
                 "=c" (ecx),
                 "=d" (edx)
               : "0" (eax), "2" (ecx));

  return (ecx & 2);
}


static inline bool hasSSE42()
{
  unsigned int ecx(0);
  unsigned int eax(1); // we want processor info and feature bits

  asm volatile("cpuid"
               : "=c"(ecx)
               : "a"(eax)
               : "%ebx", "%edx");
  return (ecx >> 20) & 1;
}


evb::CRCCalculator::CRCCalculator()
  : havePCLMULQDQ_( hasPCLMULQDQ() ),
    haveSSE42_( hasSSE42() )
{}


uint16_t evb::CRCCalculator::compute(const uint8_t* buffer, size_t bufSize) const
{
  uint16_t crc(0xffff);
  compute(crc,buffer,bufSize);
  return crc;
}


void evb::CRCCalculator::compute(uint16_t& crc, const uint8_t* buffer, size_t bufSize) const
{
  assert(0==bufSize%8);
  if ( bufSize == 0 ) return;

  if ( havePCLMULQDQ_ )
  {
    crc = crc16_T10DIF_128x_extended(crc,buffer,bufSize);
  }
  else
  {
    if (bufSize % 16 == 8)
    {
      computeCRC_32bit(crc, ((uint32_t *)buffer)[1]);
      computeCRC_32bit(crc, ((uint32_t *)buffer)[0]);
      bufSize -= 8;
      buffer += 8;
    }

    while (bufSize >= 16)
    {
      computeCRC_32bit(crc, ((uint32_t *)buffer)[1]);
      computeCRC_32bit(crc, ((uint32_t *)buffer)[0]);
      computeCRC_32bit(crc, ((uint32_t *)buffer)[3]);
      computeCRC_32bit(crc, ((uint32_t *)buffer)[2]);
      bufSize -= 16;
      buffer += 16;
    }

    if (bufSize == 8)
    {
      computeCRC_32bit(crc, ((uint32_t *)buffer)[1]);
      computeCRC_32bit(crc, ((uint32_t *)buffer)[0]);
    }
  }
}


uint32_t evb::CRCCalculator::crc32c(uint32_t crc, const unsigned char *buf, size_t len) const
{
  return haveSSE42_ ? crc32c_hw(crc, buf, len) : crc32c_sw(crc, buf, len);
}


/// emacs configuration
/// Local Variables: -
/// mode: c++ -
/// c-basic-offset: 2 -
/// indent-tabs-mode: nil -
/// End: -
