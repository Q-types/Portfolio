"""Offline run; original inputs require byte-bound established local-processing authority."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

from .features import aggregate
from .fixture import fixture_bytes
from .protocol import validate, split, learn, evaluate

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
MAX_BYTES = 4_000_000


def encoded(value):
    return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()


def identity(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def safe_path(value):
    path=Path(value).absolute()
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('symlink paths forbidden; use canonical private locations')
    return path.resolve()


def read_bounded(path):
    with path.open('rb') as stream:
        raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError('bounded adapter accepts at most 4 MB per file')
    return raw


def unique_object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate JSON key')
        result[k]=v
    return result


def decode(raw):
    return json.loads(raw,object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def gate(input_path,config_path,output_path,receipt_path):
    ip,cp,op=map(safe_path,(input_path,config_path,output_path))
    public=ip==BASE/'fixtures/synthetic.csv' and cp==BASE/'protocol.json'
    if op.exists(): raise ValueError('output must be a fresh directory')
    receipt_raw=None
    if not public:
        if receipt_path is None or any(p.is_relative_to(ROOT) for p in (ip,cp,op)):
            raise ValueError('private input/config/output and established permission required')
        rp=safe_path(receipt_path)
        if rp.is_relative_to(ROOT): raise ValueError('receipt must be private')
        receipt_raw=read_bounded(rp); receipt=decode(receipt_raw)
        if (receipt.get('authorized_local_processing') is not True
                or receipt.get('redistribution_authorized') is not False
                or receipt.get('scope')!='private_customer_segmentation'
                or any(not isinstance(receipt.get(key),str) or not receipt[key].strip()
                       for key in ['authority_reference','identity_basis','mapping_reference'])
                or receipt.get('input_path')!=str(ip) or receipt.get('config_path')!=str(cp)
                or receipt.get('output_path')!=str(op)):
            raise ValueError('receipt must bind established scope, mapping, identities and locations')
    # Read once: the SAME buffers are hashed, parsed and retained; no later input/config reopen.
    raw,config_raw=read_bounded(ip),read_bounded(cp)
    if public:
        if raw!=fixture_bytes(): raise ValueError('public input must be exact invented fixture')
    elif receipt.get('input')!=identity(raw) or receipt.get('config')!=identity(config_raw):
        raise ValueError('receipt does not bind exact consumed bytes')
    return raw,config_raw,op,public,receipt_raw


def execute(input_path,config_path,output_path,receipt_path=None):
    raw,config_raw,output,public,receipt_raw=gate(input_path,config_path,output_path,receipt_path)
    config=decode(config_raw); validate(config)
    customers,ledger=aggregate(raw,config)
    fit,evaluation=split(customers,config)
    frozen=learn(fit,config)
    frozen_raw=encoded(frozen)  # freeze all candidates and sensitivity fits before evaluation
    results=evaluate(frozen,fit,evaluation,config)
    if frozen_raw!=encoded(frozen): raise ValueError('evaluation mutated fitted state')
    source={p.name:identity(p.read_bytes()) for p in sorted(BASE.glob('*.py'))}
    run_id=identity(encoded(dict(input=identity(raw),config=identity(config_raw),source=source)))['sha256']
    files={'input.csv':raw,'config.json':config_raw,'customers.json':encoded(customers),
           'ledger.json':encoded(ledger),'frozen.json':frozen_raw,
           'evaluation.json':encoded(dict(run_id=run_id,comparisons=results,
              interpretation='Synthetic mechanics only; no business utility established' if public
                             else 'Private descriptive analysis; no business utility established'))}
    if receipt_raw is not None: files['permission_receipt.json']=receipt_raw
    manifest=dict(schema='segmentation_run_v1',run_id=run_id,
                  evidence='synthetic mechanics only' if public else 'private descriptive analysis',
                  scope='public_invented' if public else 'private_no_redistribution',
                  python=platform.python_version(),input=identity(raw),config=identity(config_raw),
                  permission_receipt=None if receipt_raw is None else identity(receipt_raw),
                  source=source,files={name:identity(content) for name,content in sorted(files.items())},
                  frozen_before_evaluation=identity(frozen_raw))
    output.mkdir(parents=True,exist_ok=False)
    for name,content in {**files,'manifest.json':encoded(manifest)}.items():
        (output/name).write_bytes(content)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=BASE/'fixtures/synthetic.csv')
    parser.add_argument('--config',type=Path,default=BASE/'protocol.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--permission-receipt',type=Path)
    args=parser.parse_args()
    try:
        manifest=execute(args.input,args.config,args.output,args.permission_receipt)
    except (ValueError,OSError,KeyError,TypeError,OverflowError) as exc:
        # Keep source rows, paths and permission details out of terminal/error logs.
        parser.exit(2,f'Run rejected ({type(exc).__name__}); inspect private contract and authority.\n')
    print('Completed:',manifest['evidence'])


if __name__=='__main__': main()
