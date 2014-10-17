# XDAQ
export XDAQ_ROOT=/opt/xdaq
#export XDAQ_ROOT=$HOME/daq/xdaq_root

export XDAQ_PLATFORM=`uname -m`
if test ".$XDAQ_PLATFORM" != ".x86_64"; then
    export XDAQ_PLATFORM=x86
fi
checkos=`$XDAQ_ROOT/config/checkos.sh`
export XDAQ_PLATFORM=$XDAQ_PLATFORM"_"$checkos

export XDAQ_LOCAL=${XDAQ_ROOT}
#export XDAQ_LOCAL=${HOME}/daq/trunk/${XDAQ_PLATFORM}
export XDAQ_DOCUMENT_ROOT=${XDAQ_ROOT}/htdocs
#export XDAQ_DOCUMENT_ROOT=${HOME}/daq/trunk/daq
export LD_LIBRARY_PATH=${XDAQ_LOCAL}/lib:${XDAQ_ROOT}/lib:${LD_LIBRARY_PATH}
export PATH=${PATH}:${XDAQ_LOCAL}/bin:${XDAQ_ROOT}/bin

# EvB tester suite
export EVB_TESTER_HOME=${HOME}/daq/trunk/daq/evb/test
export EVB_SYMBOL_MAP=standaloneSymbolMap.txt
export PATH=${PATH}:${EVB_TESTER_HOME}/scripts
export PYTHONPATH=${EVB_TESTER_HOME}/scripts:${PYTHONPATH}

ulimit -l unlimited
