"""
Checks that files duplicated across schemes/implementations are consistent.
"""

import difflib
import os
import sys

import yaml

import helpers
import pqclean

sys.tracebacklimit = 0


def pytest_generate_tests(metafunc):
    ids = []
    argvalues = []
    for scheme in pqclean.Scheme.all_schemes():
        for implementation in scheme.implementations:
            if os.path.isfile(
                    os.path.join(
                        'duplicate_consistency',
                        '{}_{}.yml'.format(scheme.name, implementation.name))):
                metafile = os.path.join(
                    'duplicate_consistency',
                    '{}_{}.yml'.format(scheme.name, implementation.name))
                with open(metafile, encoding='utf-8') as f:
                    metadata = yaml.safe_load(f.read())
                    for group in metadata['consistency_checks']:
                        source = pqclean.Implementation.by_name(
                            group['source']['scheme'],
                            group['source']['implementation'])
                        argvalues.append(
                            (implementation, source, group['files']))
                        ids.append(
                            "{metafile}: {scheme.name} {implementation.name}"
                            .format(scheme=scheme,
                                    implementation=implementation,
                                    metafile=metafile))
    metafunc.parametrize(('implementation', 'source', 'files'),
                         argvalues,
                         ids=ids)


def file_get_contents(filename):
    with open(filename) as file:
        return file.read()


@helpers.filtered_test
def test_duplicate_consistency(implementation, source, files):
    """Test sets of files to be identical modulo namespacing"""
    messages = []
    for file in files:
        target_path = os.path.join(source.path(), file)
        this_path = os.path.join(implementation.path(), file)
        target_src = file_get_contents(target_path)
        this_src = file_get_contents(this_path)
        this_transformed_src = this_src.replace(
            implementation.namespace_prefix(), '')
        target_transformed_src = target_src.replace(
            source.namespace_prefix(), '')

        if not this_transformed_src == target_transformed_src:
            diff = difflib.unified_diff(
                this_transformed_src.splitlines(keepends=True),
                target_transformed_src.splitlines(keepends=True),
                fromfile=this_path,
                tofile=target_path)
            messages.append("{} differed:\n{}".format(file, ''.join(diff)))
    if messages:
        raise AssertionError("Files differed:\n{}".format('\n'.join(messages)))


if __name__ == '__main__':
    import pytest
    pytest.main(sys.argv)
