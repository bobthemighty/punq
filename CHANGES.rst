Changelog
=========

`0.2.1`_ 2019-05-22
-------------------
Fixes
    Punq will now prefer to use a provided resolution argument instead of creating it anew.

`0.2.0`_ 2019-02-12
-------------------
Fixes
    Added handling for typing.ForwardRef

Breaking Changes
    Added explicit `instance` kwarg to `register` which replaces the previous behaviour where
    `container.register(Service, someInstance)` would register a concrete instance.
    This fixes https://github.com/bobthemighty/punq/issues/6

0.1.2-alpha 2019-02-11
----------------------
Feature
    First automatic Travis deploy

0.0.1
-----
    Basic resolution and registration works
    Punq is almost certainly slow as a dog, non thread-safe, and prone to weird behaviour in the edge cases.

.. _0.2.0: https://github.com/bobthemighty/punq/compare/v0.1.2-alpha...v0.2
.. _0.2.1: https://github.com/bobthemighty/punq/compare/v0.2...v0.2.1
