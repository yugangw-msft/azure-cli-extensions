# Azure CLI Enhanced Monitoring Extension #
This is an extension to azure cli which provides enhanced support around Azure Active Directory 

## How to use ##
First, install the extension:
```
az extension add --name aad
```

Then, call it as you would any other az command:
```
az ad user update --upn-or-object-id user1@myorg.onmicrosoft.com --display-name "John Doe"
```