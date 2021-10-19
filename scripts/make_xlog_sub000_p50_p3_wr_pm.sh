#!/usr/bin/bash

# ../mkdig/sub000c5.crw
# ../mkdig/sub000c.crw
# ../mkdig/sub000p3.crw
# ../mkdig/sub000p5.crw
# ../mkdig/sub000pm.crw
# ../mkdig/sub000rc.crw
# ../mkdig/sub000ro.crw
# ../mkdig/sub000wr.crw

# ../mkdig/p3_1025.bdf
# ../mkdig/p3.bdf
# ../mkdig/p50.bdf
# ../mkdig/picmem_1025.bdf
# ../mkdig/picmem.bdf
# ../mkdig/wrep.bdf


MKDIG="../mkdig/"

for exp in p5 p3 wr pm
do
    crwf=${MKDIG}sub000${exp}.crw
    logf=${crwf/crw/log}
    arf=${crwf/crw/arf}
    xlogf=${logf/log/x.log}
    xblf=${xlogf/log/blf}

    avgf=${MKDIG}.tmp.avg

    bdf=${MKDIG}${exp}.bdf

    # copy the xlog
    cp ${logf} ${xlogf}
    

    # generate blf
    cmd="cdbl ${bdf} ${xlogf} ${xblf} 250"
    ${cmd}

    if [ -e ${avgf} ]; then
	rm ${avgf}
    fi

    echo ${crwf} ${xlogf} ${xblf} | avg 100 ${avgf} -x -c 1 -a ${arf}

done

