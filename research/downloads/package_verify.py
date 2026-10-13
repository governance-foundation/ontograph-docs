"""Verify the complete portable package and safely unpack an externally pinned ZIP."""
import argparse
import hashlib
import json
import stat
from pathlib import Path, PurePosixPath
import zipfile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe(name):
    p = PurePosixPath(name)
    require(bool(name) and not p.is_absolute() and '\\' not in name and ':' not in name
            and all(x not in ('', '.', '..') for x in name.split('/')),
            'Unsafe package path: ' + name)
    return p


def check_members(members):
    names = list(members)
    require(len(names) <= 5000 and sum(map(len, members.values())) <= 100_000_000,
            'Package exceeds bounded member/expanded-byte budget')
    for name in names:
        safe(name)
    require(len({x.casefold() for x in names}) == len(names), 'Case-insensitive duplicate path')
    name_set = {x.casefold() for x in names}
    require(not any(parent.as_posix().casefold() in name_set for name in names for parent in PurePosixPath(name).parents if parent.as_posix() != '.'), 'File/directory prefix collision')
    require('package-manifest.json' in members and 'artifact-index.json' in members, 'Missing manifest/index')
    manifest = json.loads(members['package-manifest.json'])
    index = json.loads(members['artifact-index.json'])
    require(manifest['schemaVersion'] == 'ontograph.research.package.v1', 'Unknown package schema')
    require(index['schemaVersion'] == 'ontograph.research.evidence.v1', 'Unknown index schema')
    require(manifest['artifactIndexRef'] == 'artifact-index.json', 'Wrong index binding')
    declared = index['artifacts']
    paths = [a['path'] for a in declared]
    ids = [a['id'] for a in declared]
    require(len(set(paths)) == len(paths) and len(set(ids)) == len(ids), 'Duplicate artifact path or id')
    require(set(paths) | {'package-manifest.json', 'artifact-index.json'} == set(names), 'Missing or unallowlisted member')
    require(not {'package-manifest.json', 'artifact-index.json'} & set(paths), 'Recursive index inclusion')
    for row in declared:
        safe(row['path'])
        data = members[row['path']]
        require(len(data) == row['bytes'] and sha(data) == row['sha256'], 'Byte/digest drift: ' + row['path'])
    for ref in [manifest['journeyCommandRef'], *manifest['expectedOutcomeRefs'],
                *manifest['prerequisiteRefs'], *manifest['licenseRefs'], *manifest['claimRefs']]:
        require(ref in paths, 'Unresolved package reference: ' + ref)
    source_manifest = index.get('sourceIdentitiesRef')
    license_manifest = index.get('licenseIdentitiesRef')
    require(source_manifest and license_manifest, 'Required source/license catalogues absent')
    if source_manifest or license_manifest:
        require(source_manifest in paths and license_manifest in paths, 'Missing source/license catalogue')
        sources = json.loads(members[source_manifest])['sources']
        licenses = json.loads(members[license_manifest])['licenses']
        source_ids = [x['id'] for x in sources]
        license_ids = [x['id'] for x in licenses]
        require(len(set(source_ids)) == len(source_ids) and len(set(license_ids)) == len(license_ids), 'Duplicate source/license identity')
        require(all(a['sourceRef'] in source_ids and a['licenseRef'] in license_ids for a in declared), 'Unresolved artifact source/license identity')
        require(all(x['noticeRef'] in paths for x in licenses), 'Unresolved license notice')
    return manifest, index


def verify_root(root):
    root = root.resolve(strict=True)
    files = list(root.rglob('*'))
    require(not any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in files), 'Filesystem alias in package')
    return check_members({p.relative_to(root).as_posix(): p.read_bytes() for p in files if p.is_file()})


def unpack(archive, expected_sha, target):
    require(sha(archive.read_bytes()) == expected_sha, 'Archive external SHA-256 mismatch')
    require(not target.exists(), 'Extraction target must be absent; retain previous evidence')
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        require(len({i.filename for i in infos}) == len(infos), 'Duplicate ZIP member')
        require(sum(i.file_size for i in infos) <= 100_000_000 and len(infos) <= 5000, 'Archive size budget')
        for info in infos:
            safe(info.filename)
            require(not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16), 'Special/archive directory member')
        members = {i.filename: z.read(i) for i in infos}
    result = check_members(members)
    target.mkdir(parents=True)
    for name, data in members.items():
        path = target.joinpath(*safe(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path)
    p.add_argument('--archive', type=Path)
    p.add_argument('--sha256')
    p.add_argument('--extract', type=Path)
    a = p.parse_args()
    if a.archive:
        require(a.sha256 and a.extract and not a.root, 'Archive mode needs --sha256 --extract only')
        manifest, index = unpack(a.archive, a.sha256, a.extract)
    else:
        require(a.root and not a.extract and not a.sha256, 'Use --root or complete archive mode')
        manifest, index = verify_root(a.root)
    print(json.dumps({'packageRef': manifest['packageRef'], 'verifiedArtifacts': len(index['artifacts']),
                      'outcome': 'passed', 'runtimeExecuted': False}, sort_keys=True))


if __name__ == '__main__':
    main()
