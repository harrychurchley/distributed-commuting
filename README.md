# distributed-commuting
A tool which draw an isochrone around a coordinate, and return houses listed on rightmove that sit within the polygon. See [example.ipynb](https://github.com/harrychurchley/distributed-commuting/blob/main/example.ipynb) for usage example.

### steps

- [x] recieve a postcode
- [x] draw isochrone
- [x] find furthest point from postcode-isochrone
- [x] find distance between these points
- [x] round up to nearest rightmove search dist
- [x] formulate rightmove URL - postcode to region_code
- [x] search rightmove for properties within rounded distance
- [x] rightmove address data to lat/long
- [x] work out which properties are within isochrone
- [x] map