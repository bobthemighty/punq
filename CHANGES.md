## [0.2.0] 2019-02-12
### Fixes https://github.com/bobthemighty/punq/issues/9
    - Added handling for typing.ForwardRef

## [0.1.0] 2019-02-11
### Breaking Changes
    - Added explicit `instance` kwarg to `register` which replaces the previous behaviour where
      `container.register(Service, someInstance)` would register a concrete instance.
      This fixes https://github.com/bobthemighty/punq/issues/6


## 0.0.1
	- Basic resolution and registration works
	- Punq is almost certainly slow as a dog, non thread-safe, and prone to weird behaviour in the edge cases.
