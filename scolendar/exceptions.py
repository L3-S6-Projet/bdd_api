class TeacherInChargeError(Exception):
    def __init__(self, message: str = ''):
        """
        Creates a new instance of this exception.

        This particular exception should be raised when a teacher is in charge of a particular subject, but the user is
        trying to remove it from that same subject. This should be allowed, hence, this exception. Note that this
        exception extends from the generic Exception type, which allows it to behave like any other exception, thus
        being highly convenient.

        :param message: A specific message associated with this exception. This should be passed for in-place specific
                        details, which may be useful to the caller. It is marked as optional, but should probably always
                        be specified.
        """
        # Call the Exception.__init__ method, which confirms the contract created
        # when extending the Exception class.
        # This makes this custom exception behave as a regular one.
        super().__init__(message)
