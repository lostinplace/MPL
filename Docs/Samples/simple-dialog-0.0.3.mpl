Where is the X?: machine
    a: Conversant
    b: Conversant

    * -@ tries = 5

    stage: state
        start
        response ready
        response appropriate
        response provided
        response acknowledged

    b <heard> {`Where is the {$location}?`, a} &  *
        \-@ start = $location

    start $location
        \-@ b#query location($location) -@ queried location = $location

    b <knows location near> queried location, $response:string
        \-@ location response = $response -> response ready

    response ready -> !intersect(location response, tried locations) -> response appropriate
    response ready -> intersect(location response, tried locations) -> tries > 0 -@ tries -= 1 -> start
    response ready -> intersect(location response, tried locations) -> tries <= 0 -> b#say(`I can't help you`)

    a <heard> `I can't help you`, b
        \-@ a#say(`that's ok, I'll keep looking`) -@ <gave up>

    <gave up> & self -> *

    response appropriate -@ b#say(f`the {queried location} is near the {location response}`) -> response provided

    a <heard> {`thanks, that helps a lot!`, b} & response provided
        \-> response acknowledged

    response provided & b <heard> `I don't know either of those locations`, a
        \-> start

    response acknowledged & this -@ b#say(`glad I could help`) -> *



Conversant: machine
    query location =#= $location -> external({self, string}, string) -@ <knows location near> $location, $
    remember location near location =#= external({self, string, string}, string) -@ <remember> $

    self <knows location near> $location, $err:error -@ say(`I can't help you`)

    $other:Conversant <phrase> $message ~@ <heard> $message, $other
    say =#= $message -@ <phrase> $message

    self <heard> f`the {$location 1} is near the {$location 2}`
        \-@ remember location near location($location 1, $location 2)

    self <remember> `don't know either` -@ say(`I don't know either of those locations`)
    self <remember> `already knew that` -> *
    self <remember> `ok` -@ say(`thanks, that helps a lot!`)
