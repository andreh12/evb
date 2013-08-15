#!/bin/sh

# Launch executive processes
sendCmdToLauncher EVM0_SOAP_HOST_NAME EVM0_LAUNCHER_PORT STARTXDAQEVM0_SOAP_PORT
sendCmdToLauncher RU0_SOAP_HOST_NAME RU0_LAUNCHER_PORT STARTXDAQRU0_SOAP_PORT
sendCmdToLauncher BU0_SOAP_HOST_NAME BU0_LAUNCHER_PORT STARTXDAQBU0_SOAP_PORT

# Check that executives are listening
if ! webPingXDAQ EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT 5
then
  echo "Test failed"
  exit 1
fi
if ! webPingXDAQ RU0_SOAP_HOST_NAME RU0_SOAP_PORT 5
then
  echo "Test failed"
  exit 1
fi
if ! webPingXDAQ BU0_SOAP_HOST_NAME BU0_SOAP_PORT 5
then
  echo "Test failed"
  exit 1
fi

# Configure all executives
sendCmdToExecutive EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT configure.cmd.xml
sendCmdToExecutive RU0_SOAP_HOST_NAME RU0_SOAP_PORT configure.cmd.xml
sendCmdToExecutive BU0_SOAP_HOST_NAME BU0_SOAP_PORT configure.cmd.xml

# Configure and enable ptatcp
sendSimpleCmdToApp EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT pt::atcp::PeerTransportATCP 0 Configure
sendSimpleCmdToApp RU0_SOAP_HOST_NAME RU0_SOAP_PORT pt::atcp::PeerTransportATCP 1 Configure
sendSimpleCmdToApp BU0_SOAP_HOST_NAME BU0_SOAP_PORT pt::atcp::PeerTransportATCP 2 Configure
sendSimpleCmdToApp EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT pt::atcp::PeerTransportATCP 0 Enable
sendSimpleCmdToApp RU0_SOAP_HOST_NAME RU0_SOAP_PORT pt::atcp::PeerTransportATCP 1 Enable
sendSimpleCmdToApp BU0_SOAP_HOST_NAME BU0_SOAP_PORT pt::atcp::PeerTransportATCP 2 Enable

# Configure all applications
sendSimpleCmdToApp EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT evb::EVM 0 Configure
sendSimpleCmdToApp RU0_SOAP_HOST_NAME RU0_SOAP_PORT evb::RU 0 Configure
sendSimpleCmdToApp BU0_SOAP_HOST_NAME BU0_SOAP_PORT evb::BU 0 Configure

sleep 1

#Enable EVM
sendSimpleCmdToApp EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT evb::EVM 0 Enable

#Enable RU
sendSimpleCmdToApp RU0_SOAP_HOST_NAME RU0_SOAP_PORT evb::RU 0 Enable

#Enable BUs
sendSimpleCmdToApp BU0_SOAP_HOST_NAME BU0_SOAP_PORT evb::BU 0 Enable

echo "Sending data for 5 seconds"
sleep 5

superFragmentSizeEVM=`getParam EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT evb::EVM 0 superFragmentSize xsd:unsignedInt`
echo "EVM superFragmentSize: $superFragmentSizeEVM"
if [[ $superFragmentSizeEVM -ne 12288 ]]
then
  echo "Test failed: expected 12288"
  exit 1
fi

superFragmentSizeRU0=`getParam RU0_SOAP_HOST_NAME RU0_SOAP_PORT evb::RU 0 superFragmentSize xsd:unsignedInt`
echo "RU0 superFragmentSize: $superFragmentSizeRU0"
if [[ $superFragmentSizeRU0 -ne 16384 ]]
then
  echo "Test failed: expected 16384"
  exit 1
fi

eventRateEVM=`getParam EVM0_SOAP_HOST_NAME EVM0_SOAP_PORT evb::EVM 0 eventRate xsd:unsignedInt`
echo "EVM eventRate: $eventRateEVM"
if [[ $eventRateEVM -lt 1000 ]]
then
  echo "Test failed"
  exit 1
fi

nbEventsBuiltBU0=`getParam BU0_SOAP_HOST_NAME BU0_SOAP_PORT evb::BU 0 nbEventsBuilt xsd:unsignedInt`
echo "BU0 nbEventsBuilt: $nbEventsBuiltBU0"
if [[ $nbEventsBuiltBU0 -lt 1000 ]]
then
  echo "Test failed"
  exit 1
fi

eventSizeBU0=`getParam BU0_SOAP_HOST_NAME BU0_SOAP_PORT evb::BU 0 eventSize xsd:unsignedInt`
echo "BU0 eventSize: $eventSizeBU0"
if [[ $eventSizeBU0 -ne 28672 ]]
then
  echo "Test failed: expected 28672"
  exit 1
fi

echo "Test launched successfully"
exit 0