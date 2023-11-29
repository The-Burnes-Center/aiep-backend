# API Message Models

### Uploading a File:
```
file binary data // ws.send(event.target.result)*;

+

{ type: "language", data: selectedLanguage }
```

*The read-only target property of the Event interface is a reference to the object onto which the event was dispatched. It is different from Event.currentTarget when the event handler is called during the bubbling or capturing phase of the event.

### Sending a Message:
```
{ type: "message", data: str }
```

### All ChatBot Generated Messages follow the format:
```
{ type: "response", message: str }
```

