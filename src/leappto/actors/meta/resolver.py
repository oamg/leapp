from . import registry, _fq


def resolve(services):
    lookup = {_fq(s): s.leapp_meta() for s in services}
    for s in services:
        m = lookup[_fq(s)]
        for link in  m.get('address_links', []):
            tgtm = lookup[link['target']]
            tgtm['fixup'] = tgtm.get('fixup', []) + [(s, link)]
            tgtm['require_links'] = tgtm.get('require_links', []) + [{'target': _fq(s)}]


def dependency_ordered(services):
    result = []
    result_fq = []
    for s in services:
        if not s.leapp_meta().get('require_links', []):
            result.append(s)
            result_fq.append(_fq(s))

    services = [s for s in services if s not in result]
    count = len(services)
    while services and count > 0:
        count -= 1
        for s in services:
            if all([link['target'] in result_fq for link in s.leapp_meta().get('require_links', [])]):
                result.append(s)
                result_fq.append(_fq(s))
        services = [s for s in services if s not in result]
    result += services
    return result
