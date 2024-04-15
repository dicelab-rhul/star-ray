from star_ray.plugin.xml import xml_change_tracker


@xml_change_tracker
class MyClass:

    def notify(self, event):
        pass


print([MyClass] + list(MyClass.__bases__))
