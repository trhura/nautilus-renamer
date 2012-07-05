#! /usr/bin/python
#  -*- coding: utf-8 -*-

import imp
import re
import unittest
renamer = imp.load_source ('renamer', 'nautilus-renamer.py')

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.app = renamer.RenameApplication ()
        self.files1 = ['a.jpg','b.jpg','c.jpg', 'd.jpg']
        self.files2 = ['123abc.jpg','4321dcba.jpg']

    def _test_pattern (self, pattern, files, outfiles):
        # make sure the shuffled sequence does not lose any elements
        self.app.pattern = pattern
        self.app.substitute_p = False
        for index, match in enumerate(self.app.ran_pat.finditer (self.app.pattern)):
            start = match.groupdict ().get ('start')
            end = match.groupdict ().get ('end')
            self.app.ran_seq[str(index)] = [x for x in xrange (int(start), int(end) + 1)]
        lst = [self.app._get_new_name (fil) for fil in files]
        self.assertEqual (lst, outfiles)

    def _test_substitute (self, pattern, replee, repler, files, outfiles):
        self.app.replees = replee.split ('/')
        self.app.replers = repler.split ('/')
        self.app.substitute_p = True
        self.app.pattern = pattern
        lst = [self.app._get_new_name (fil) for fil in files]
        self.assertEqual (lst, outfiles)

    def test_random (self):
        self.app.pattern = '/rand,5-8/-/rand,1000-2000/-/rand,20-90/'
        self.app.substitute_p = False
        for index, match in enumerate(self.app.ran_pat.finditer (self.app.pattern)):
            start = match.groupdict ().get ('start')
            end = match.groupdict ().get ('end')
            self.app.ran_seq[str(index)] = [x for x in xrange (int(start), int(end) + 1)]
        for item in [self.app._get_new_name (fil) for fil in self.files1]:
            #print '\n%s = %s' %(self.app.pattern, item)
            self.assertIsNotNone (re.search ('\d{1}-\d{4}-\d{2}', item))

    def test_pattern1 (self):
        self._test_pattern ('/name//num,5//num,3+5//ext/',
                            self.files1,
                            ['a00001005.jpg',
                             'b00002006.jpg',
                             'c00003007.jpg',
                             'd00004008.jpg'])
    def test_pattern2 (self):
        self._test_pattern ('/num,12+100//filename/',
                            self.files1,
                            ['000000000100a.jpg',
                             '000000000101b.jpg',
                             '000000000102c.jpg',
                             '000000000103d.jpg',
                            ])
    def test_pattern3 (self):
        self._test_pattern ('/filename,3/',
                            self.files2,
                            ['abc.jpg',
                             '1dcba.jpg'
                            ])

    def test_pattern4 (self):
        self._test_pattern ('/name,-3/',
                            self.files2,
                            ['abc',
                             'cba',
                            ])

    def test_pattern5 (self):
        self._test_pattern ('/name,-3:-100/',
                            self.files2,
                            ['123',
                             '4321d',
                            ])

    def test_substitute (self):
        self._test_substitute ('/name//num,5//num,3+5//ext/',
                               '0',
                               'o',
                               self.files1,
                               ['aoooo1oo5.jpg',
                                'boooo2oo6.jpg',
                                'coooo3oo7.jpg',
                                'doooo4oo8.jpg'])

    def test_substitute2 (self):
        self._test_substitute ('/name//num,5//num,3+5//ext/',
                               '0',
                               'o',
                               self.files1,
                               ['aoooo1oo5.jpg',
                                'boooo2oo6.jpg',
                                'coooo3oo7.jpg',
                                'doooo4oo8.jpg'])

    def test_substitute3 (self):
        self._test_substitute ('/name/-/num,5/-a/ext/',
                               '-/0/a',
                               '_/o',
                               self.files1,
                               ['o_oooo1_o.jpg',
                                'b_oooo2_o.jpg',
                                'c_oooo3_o.jpg',
                                'd_oooo4_o.jpg'])

if __name__ == '__main__':
    unittest.main()
