from . import registry, _fq

def resolve(services):
    lookup = {_fq(s): s.leapp_meta() for s in services}
    for s in services:
        m = lookup[_fq(s)]
        for link in  m.get('address_links', []):
            tgtm = lookup[link['target']].leapp_meta()
            tgtm['fixup'] = tgtm.get('fixup', []) + [(s, link)]
            tgtm['require_links'] = tgtm.get('require_links', []) + [_fq(s)]

