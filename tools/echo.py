class EchoTool:
    name = "echo"
    def invoke(self, text):
        return f"Echo: {text}"

echo_tool = EchoTool()
