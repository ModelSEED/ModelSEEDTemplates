#!/usr/bin/env python

import biokbase.workspace.baseclient as baseclient
from biokbase.workspace.client import Workspace

Workspace_URL = 'https://kbase.us/services/ws'
WSClient = Workspace(url = Workspace_URL)# , token = Token)
print('WS Client instantiated: Version '+WSClient.ver())

Output = WSClient.get_module_info({'mod': 'KBaseFBA'})
with open("KBaseFBA.spec",'w') as kfs_fh:
    kfs_fh.write(Output['spec'])
