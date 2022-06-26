class Code:
    def __init__(self, id, description):
        self.id = id
        self.description = description

CODE_EQUIPMENT_NOT_FOUND = Code("01", "Equipment not found")
CODE_SOURCE_EQUIPMENT_NOT_FOUND = Code("02", "Source equipment not found")
CODE_TARGET_EQUIPMENT_NOT_FOUND = Code("03", "Target equipment not found")
CODE_EQUIPMENT_LIMIT_EXCEEDED = Code("04", "Equipment limit exceeded")

CODE_SUCCESSFUL_REMOVAL = Code("01", "Successful removal")
