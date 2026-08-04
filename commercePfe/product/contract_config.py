# contract_config.py
from web3 import Web3
from django.conf import settings

# Connect to blockchain
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))  # or use settings.BLOCKCHAIN_URL

# Contract details
contract_address = '0x3992028669E3a64073a761f2dE007a3651009Af6'  # Should be in settings ideally

contract_abi = [
     {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "seller",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "clientEmail",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "clientData",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "finalpayload",
          "type": "string"
        }
      ],
      "name": "OrderPlaced",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "enum Purchase.Status",
          "name": "newStatus",
          "type": "uint8"
        }
      ],
      "name": "OrderStatusUpdated",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "enum Purchase.Status",
          "name": "newStatus",
          "type": "uint8"
        }
      ],
      "name": "PaymentStatusUpdated",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "orderCount",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "orders",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "seller",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "totalPrice",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "clientEmail",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "clientData",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "finalpayload",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        },
        {
          "internalType": "enum Purchase.Status",
          "name": "paymentStatus",
          "type": "uint8"
        },
        {
          "internalType": "enum Purchase.Status",
          "name": "deliveryStatus",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "orderId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "seller",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "totalPrice",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "clientEmail",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "clientData",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "finalpayload",
          "type": "string"
        }
      ],
      "name": "placeOrder",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "orderId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "deliveryInProgress",
          "type": "string"
        }
      ],
      "name": "markInProgress",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "orderId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "deliveryNotConfirm",
          "type": "string"
        }
      ],
      "name": "markDelivered",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "orderId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "finalConfirmation",
          "type": "string"
        }
      ],
      "name": "confirmDelivery",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "orderId",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "deliveryCancelledInfo",
          "type": "string"
        }
      ],
      "name": "deliveryCancelled",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]

# Instantiate the contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Get the account from the private key
private_key = settings.ETH_PRIVATE_KEY
account = w3.eth.account.from_key(private_key)
