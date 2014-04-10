Watch gerrit (2.8) changes and show them to err.

I am not sure why config is not working for me so you probably have to hack
`BASE_URL` yourself to your gerrit (it sucks atm but i'll probably fix that
properly in the future).

you have the command !gerrit add to add some routing to some channel, for example:

!gerrit add project room1, room2

will send all the new change of project to room1 and room2

!gerrit list would list those

Some of the code i have here is pretty crappy and i'm just too lazy to code it.

It was made under python3.x
