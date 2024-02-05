### Mouse Tracker Example

A very simple example of an application that uses icua2's built-in XML/SVG environment. It simply visualises a circle which changes its properties based on user input. An interface is shown to the user via the `SVGAvatar` class. User input is converted to `QueryXML` events which directly modify the environment XML state. These changes are reflected in the interface which the avatar presents. 

User input makes the following changes to the environment state:
- Mouse clicking will shrink/enlarge the circle.
- Key pressing will randomly change the colour of the circle.
- Mouse motion will move the circle to the new position.
- Exiting the interface is also handled gracefully - causes the environment to exit.
