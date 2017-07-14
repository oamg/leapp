#from wowp.components import InPort

class Any(object):
    """A unique wildcard object

    Note that we cannot use None as this can be used by users
    """

    def __init__(self):
        raise Exception('Any cannot be instantiated')

class PortAnnotation(object):
    def __init__(self, msgtype):
        self.msgtype = msgtype


class DstPortAnnotation(PortAnnotation):
    def __init__(self, msgtype, srcname=Any):
        super(DstPortAnnotation, self).__init__(msgtype)
        self.srcname = srcname

#class AnnotatedInPort(InPort):
#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)


def matchport(inport, outport):
    try:
        return (issubclass(outport.annotation.msgtype, inport.annotation.msgtype) and
                (inport.annotation.srcname == Any or outport.owner.name == inport.annotation.srcname ))
    except AttributeError:
        #print('Warning: no annotation in ', str(inport), " or ", str(outport))
        return False

class MsgType(object):
    def __init__(self, srcname, errorinfo, payload):
        self.srcname=srcname
        self.errorinfo=errorinfo
        self.payload=payload

def connectactors(actors):
    allinports=[p for a in actors for p in a.inports.values()]
    alloutports=[p for a in actors for p in a.outports.values()]

    for ip in allinports:
        opcount = 0
        for op in alloutports:
            if matchport(ip, op):
                print("matched! ", ip)
                opcount += 1
                ip += op
                # we do not want to have more than one output port connected to one input port
                # break
        if opcount > 1:
            print("Warning: input port ", ip, "has {} output ports".format(opcount) )
