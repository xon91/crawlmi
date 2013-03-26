from twisted.trial import unittest

from crawlmi.utils.misc import arg_to_iter, load_object, iter_submodules


class UtilsMiscTest(unittest.TestCase):

    def test_load_object(self):
        obj = load_object('crawlmi.utils.misc.load_object')
        self.assertIs(obj, load_object)
        self.assertRaises(ImportError, load_object, 'nomodule999.mod.function')
        self.assertRaises(NameError, load_object, 'crawlmi.utils.misc.load_object999')

    def test_arg_to_iter(self):
        self.assertTrue(hasattr(arg_to_iter(None), '__iter__'))
        self.assertTrue(hasattr(arg_to_iter(100), '__iter__'))
        self.assertTrue(hasattr(arg_to_iter('lala'), '__iter__'))
        self.assertTrue(hasattr(arg_to_iter([1, 2, 3]), '__iter__'))
        self.assertTrue(hasattr(arg_to_iter(l for l in 'abcd'), '__iter__'))

        self.assertEqual(list(arg_to_iter(None)), [])
        self.assertEqual(list(arg_to_iter('lala')), ['lala'])
        self.assertEqual(list(arg_to_iter(100)), [100])
        self.assertEqual(list(arg_to_iter(l for l in 'abc')), ['a', 'b', 'c'])
        self.assertEqual(list(arg_to_iter([1, 2, 3])), [1, 2, 3])
        self.assertEqual(list(arg_to_iter({'a': 1})), [{'a': 1}])

    def test_iter_submodules(self):
        mods = iter_submodules('crawlmi.tests.test_utils.test_iter_submodules')
        expected = [
            'crawlmi.tests.test_utils.test_iter_submodules',
            'crawlmi.tests.test_utils.test_iter_submodules.mod',
            'crawlmi.tests.test_utils.test_iter_submodules.mod.mod0',
            'crawlmi.tests.test_utils.test_iter_submodules.mod1',
        ]
        self.assertSetEqual(set([m.__name__ for m in mods]), set(expected))

        mods = iter_submodules('crawlmi.tests.test_utils.test_iter_submodules.mod')
        expected = [
            'crawlmi.tests.test_utils.test_iter_submodules.mod',
            'crawlmi.tests.test_utils.test_iter_submodules.mod.mod0',
        ]
        self.assertSetEqual(set([m.__name__ for m in mods]), set(expected))

        mods = iter_submodules('crawlmi.tests.test_utils.test_iter_submodules.mod1')
        expected = [
            'crawlmi.tests.test_utils.test_iter_submodules.mod1',
        ]
        self.assertSetEqual(set([m.__name__ for m in mods]), set(expected))

        self.assertRaises(ImportError, iter_submodules, 'nomodule999')
