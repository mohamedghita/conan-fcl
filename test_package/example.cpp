#include <fcl/shape/geometric_shapes.h>
#include <cassert>

int main() {
  assert(fcl::Box(1, 1, 1).computeVolume() == 1);
}