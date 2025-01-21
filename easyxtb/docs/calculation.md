All calculations are run using the core `Calculation` object.

Manually initializing it allows for careful setup of the options that should be passed to `xtb` or `crest` on the command line, but is somewhat time-consuming.

For convenience, therefore, various class methods are made available that construct appropriate `Calculation` objects for specific runtypes, with method names corresponding to the respective `xtb` or `crest` runtypes.

::: easyxtb.Calculation
    options:
      heading_level: 2
      members_order: source
