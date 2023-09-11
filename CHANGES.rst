Changelog
=========
`0.7.0`_ 2023-09-11
-------------------
    Dropped Python3.7 support.
    

`0.6.0`_ 2022-02-15
-------------------
    Replaced pipenv and Makefiles on Travis with this Hypermodern gubbins on
    Github Actions.

Deprecated
    The types `MissingDependencyException`, `InvalidForwardReferenceException`, and
    `InvalidRegistrationException` have been given the flake8 compatible names,
    `MissingDependencyError`, `InvalidForwardReferenceError`, and
    `InvalidRegistrationError` respectively.

    The original classes are still present and usable, but will be removed from the
    code with the upcoming 1.0 release.

`0.4.1`_ 2020-02-01
-------------------
    The container now includes itself as a dependency. This makes some funky
    use-cases simple to implement, eg. dynamic dispatch to multiple
    implementations.

`0.4.0`_ 2020-02-01
-------------------
    Punq now supports registering implementations as singleton. Singleton
    instances are cached per-container, and instantiation is lazy, ie. we defer
    creation until we first resolve the service.
    Hat tip to `jbcpollak`_

`0.3.0`_ 2019-07-13
-------------------
Fixes
    Punq only passes required arguments to nested dependencies. Previously, we would pass
    all the arguments in our context as kwargs, which caused unintuitive failures if constructors
    weren't expecting them.
    Fixed by `Thielen B`_

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
.. _0.3.0: https://github.com/bobthemighty/punq/compare/v0.2.1...v0.3.0
.. _0.4.0: https://github.com/bobthemighty/punq/compare/v0.3.0...v0.4.0
.. _0.4.1: https://github.com/bobthemighty/punq/compare/v0.4.0...v0.4.1
.. _0.6.0: https://github.com/bobthemighty/punq/compare/v0.4.1...v0.6.0
.. _Thielen B: https://github.com/FourSpotProject
.. _jbcpollak: https://github.com/jbcpollak
