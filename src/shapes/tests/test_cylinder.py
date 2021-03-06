import mitsuba
import pytest
import enoki as ek
from enoki.dynamic import Float32 as Float


def example_disk(scale = (1, 1, 1), translate = (0, 0, 0)):
    from mitsuba.core.xml import load_string
    return load_string("""<shape version="2.0.0" type="cylinder">
        <transform name="to_world">
            <scale x="{}" y="{}" z="{}"/>
            <translate x="{}" y="{}" z="{}"/>
        </transform>
    </shape>""".format(scale[0], scale[1], scale[2],
                       translate[0], translate[1], translate[2]))

def example_scene(scale = (1, 1, 1), translate = (0, 0, 0)):
    from mitsuba.core.xml import load_string
    return load_string("""<scene version='2.0.0'>
        <shape type="cylinder">
            <transform name="to_world">
                <scale x="{}" y="{}" z="{}"/>
                <translate x="{}" y="{}" z="{}"/>
            </transform>
        </shape>
    </scene>""".format(scale[0], scale[1], scale[2],
                       translate[0], translate[1], translate[2]))


def test01_create(variant_scalar_rgb):
    if mitsuba.core.MTS_ENABLE_EMBREE:
        pytest.skip("EMBREE enabled")

    s = example_disk()
    assert s is not None
    assert s.primitive_count() == 1
    assert ek.allclose(s.surface_area(), 2*ek.pi)


def test02_bbox(variant_scalar_rgb):
    from mitsuba.core import Vector3f

    if mitsuba.core.MTS_ENABLE_EMBREE:
        pytest.skip("EMBREE enabled")

    for l in [1, 5]:
        for r in [1, 2, 4]:
            s = example_disk((r, r, l))
            b = s.bbox()

            assert ek.allclose(s.surface_area(), 2*ek.pi*r*l)
            assert b.valid()
            assert ek.allclose(b.min, -Vector3f([r, r, 0.0]))
            assert ek.allclose(b.max,  Vector3f([r, r, l]))


def test03_ray_intersect(variant_scalar_rgb):
    from mitsuba.core import Ray3f

    if mitsuba.core.MTS_ENABLE_EMBREE:
        pytest.skip("EMBREE enabled")

    for r in [1, 2, 4]:
        for l in [1, 5]:
            s = example_scene((r, r, l))

            # grid size
            n = 10

            xx = ek.linspace(Float, -1, 1, n)
            zz = ek.linspace(Float, -1, 1, n)

            for x in xx:
                for z in zz:
                    x = 1.1*r*x
                    z = 1.1*l*z

                    ray = Ray3f(o=[x, -10, z], d=[0, 1, 0],
                                time=0.0, wavelengths=[])
                    si_found = s.ray_test(ray)
                    si = s.ray_intersect(ray)

                    assert si_found == si.is_valid()
                    assert si_found == ek.allclose(si.p[0]**2 + si.p[1]**2, r**2)

                    if  si_found:
                        ray = Ray3f(o=[x, -10, z], d=[0, 1, 0],
                                    time=0.0, wavelengths=[])

                        si = s.ray_intersect(ray)
                        ray_u = Ray3f(ray)
                        ray_v = Ray3f(ray)
                        eps = 1e-4
                        ray_u.o += si.dp_du * eps
                        ray_v.o += si.dp_dv * eps
                        si_u = s.ray_intersect(ray_u)
                        si_v = s.ray_intersect(ray_v)

                        dn = si.shape.normal_derivative(si, True, True)

                        if si_u.is_valid():
                            dp_du = (si_u.p - si.p) / eps
                            dn_du = (si_u.n - si.n) / eps
                            assert ek.allclose(dp_du, si.dp_du, atol=2e-2)
                            assert ek.allclose(dn_du, dn[0], atol=2e-2)
                        if si_v.is_valid():
                            dp_dv = (si_v.p - si.p) / eps
                            dn_dv = (si_v.n - si.n) / eps
                            assert ek.allclose(dp_dv, si.dp_dv, atol=2e-2)
                            assert ek.allclose(dn_dv, dn[1], atol=2e-2)
