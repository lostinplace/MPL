Checkout: machine
    Consumer:  account
    Merchant:  account
    Item: offer

    timeout: state = 5m
    this <x: any> -> within(x, timeout) -> this <Keepalive Timeout>

    Consumer & Merchant & Item ~> Get Payment Information

    Get Payment Information: machine
        ..Consumer.PaymentInformation ~> PaymentInformation
        PaymentInformation = Consumer.PaymentInformation -> Success
        !PaymentInformation -> Collect Information
        Collect Information -> Receive Information
        Receive Information -> Validate Information
        Validate Information -> ..Consumer.PaymentInformation

        Validate Information | Receive Information | Collect Information ->
            this: Checkout <Keepalive Timeout> -> Failure

        Failure -> ..Failure
        Success -> ..Charge Customer

    Charge Customer: machine
        * -> tax = @external:CalculateTax(..Consumer, ..Merchant)
            ~> Calculated Cost = ..Item.Price * tax

        Calculated Cost@Cost -> Charge Customer
        Charge Customer ->
            Create Request = @external:CreateRequest(..:PaymentInformation, @Cost)
        Create Request ~> ..this: Checkout <Send Payment Request> {}
        Create Request -> Request Sent
        Request Sent ->
            _:PaymentProcessor <Payment Request Response> @Response:PaymentResponse ->
                Response Received
        Response Received & Response Received.success -> Success
        Response Received & Response Received.failure ->
            ..Solicit User Choice = Response Received
        Success -> ..Update Access

    Update Access: machine
        Create Access Record = @external:createAccessRecord(
            account=..Consumer, offer=..Item,)
            time= Update Access:{Payment Response}.time) ->
                Save Access Record

        Save Access Record & Save Access Record.Failure ->
            ..Inform User = Save Access Record

        Save Access Record & !Save Access Record.Failure ->
            Confirm New Access

        Confirm New Access -> Success

        Confirm New Access & Confirm New Access.Failure
            -> ..Inform User = Confirm New Access

        Success -> ..Success

        this: Checkout <Keepalive Timeout> ->
            ..Inform User `Timeout While Updating Access {Update Access}`

    Inform User -> Rollback Payment

    Rollback Payment -> Rollback In-Progress

    Rollback In-Progress ~> this <Rollback Request> {}: Payment Response

    Rollback In-Progress -> this <Keepalive Timeout> -> Rollback Payment

    Payment Processor <Rollback Response> response -> {}.state = `success` -> Failure

    Payment Processor <Rollback Response> response -> {}.state != `success` ->
        RollBack Payment