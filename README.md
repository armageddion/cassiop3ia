# Cassiop3ia
Alfr3d-MKVI 

## New Architecture
This new incarnation of Alfr3d is built using Kafka as the main message bus

### Kafka konfigs
Kafka must be running and the following topics need to exist:
- speak
- environment
- device
- user

## Services
Following is the list of services available in Alfr3d

### alfr3d-speak
Service that processes all speech functions. It subscribes to Kafka topic "speak" and listens for all messages as strings to be spoken

### alfr3d-device 
Service that handles all devices on localnet

### alfr3d-environment
Service that does all the geoloc stuff: location, weather, etc..

## Environment variables
Alfr3d is designed to get most of its configs from environment variables... suggest storing API keys there.