### ansys-api-edb gRPC Interface Package

This repository provides the auto-generated gRPC Python interface files for
the Ansys Edb Service.


#### Installation

Provided that these wheels have been published to public PyPI, they can be
installed with:

```
pip install ansys-api-edb
```

#### Build

To build the gRPC packages, run:

```
pip install build
python -m build
```

This will create both the source distribution containing just the protofiles
along with the wheel containing the protofiles and build Python interface
files.
