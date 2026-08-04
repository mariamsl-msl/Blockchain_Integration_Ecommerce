// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Purchase {
    enum PaymentStatus {NotPaid, Paid, Refunded}
    
    enum DeliveryStatus {NotDelivered, InProgress, DeliveredNotConfirm, DeliveredConfirm, Cancelled, ReturnRequested}

    struct Order {
        uint id;
        string seller;
        string totalPrice;
        string clientEmail;
        string clientData;
        string finalpayload;
        uint256 timestamp;
        PaymentStatus paymentStatus;
        DeliveryStatus deliveryStatus;
        string returnReason;
    }
    mapping(uint => Order) public orders;
    uint public orderCount;

    event OrderPlaced(uint id, string seller, string clientEmail, string clientData, string finalpayload);
    event PaymentStatusUpdated(uint id, PaymentStatus newStatus);
    event DeliveryStatusUpdated(uint id, DeliveryStatus newStatus);
    event ReturnRequestedEvent(uint id, string reason);

    function placeOrder(
        uint orderId,
        string memory seller,
        string memory totalPrice,
        string memory clientEmail,
        string memory clientData,
        string memory finalpayload
    ) public {
        orders[orderId] = Order({
            id: orderId,
            seller: seller,
            totalPrice: totalPrice,
            clientEmail: clientEmail,
            clientData: clientData,
            finalpayload: finalpayload,
            timestamp: block.timestamp,
            paymentStatus: PaymentStatus.NotPaid, 
            deliveryStatus: DeliveryStatus.NotDelivered, 
            returnReason: ""
        });

        if (orderId > orderCount) {
            orderCount = orderId;
        }

        emit OrderPlaced(orderId, seller, clientEmail, clientData, finalpayload);
    }

    function markInProgress(uint orderId, string memory deliveryInProgress) public {
        require(orderId > 0 && orderId <= orderCount, "Invalid order");
        require(orders[orderId].deliveryStatus == DeliveryStatus.NotDelivered, "Order must be not delivered");
        require(orders[orderId].paymentStatus == PaymentStatus.NotPaid, "Payment must not be confirmed");

        orders[orderId].deliveryStatus = DeliveryStatus.InProgress;
        emit DeliveryStatusUpdated(orderId, DeliveryStatus.InProgress);
    }

    function markDelivered(uint orderId, string memory deliveryNotConfirm) public {
        require(orderId > 0 && orderId <= orderCount, "Invalid order");
        require(orders[orderId].deliveryStatus == DeliveryStatus.InProgress, "Order must be in progress");
        require(orders[orderId].paymentStatus == PaymentStatus.NotPaid, "Payment must be not confirmed");

        orders[orderId].deliveryStatus = DeliveryStatus.DeliveredNotConfirm;
        emit DeliveryStatusUpdated(orderId, DeliveryStatus.DeliveredNotConfirm);
    }

    function confirmDelivery(uint orderId, string memory finalConfirmation) public {
        require(orderId > 0 && orderId <= orderCount, "Invalid order");
        require(orders[orderId].deliveryStatus == DeliveryStatus.DeliveredNotConfirm, "Order must be delivered but not yet confirmed");
        require(orders[orderId].paymentStatus == PaymentStatus.NotPaid, "Payment must be not confirmed");

        orders[orderId].deliveryStatus = DeliveryStatus.DeliveredConfirm;
        orders[orderId].paymentStatus = PaymentStatus.Paid;
        emit DeliveryStatusUpdated(orderId, DeliveryStatus.DeliveredConfirm);
        emit PaymentStatusUpdated(orderId, PaymentStatus.Paid);
    }

    function deliveryCancelled(uint orderId, string memory deliveryCancelledInfo) public {
        require(orderId > 0 && orderId <= orderCount, "Invalid order");
        require(orders[orderId].deliveryStatus == DeliveryStatus.NotDelivered, "Order can only be cancelled from NotDelivered status");
        require(orders[orderId].paymentStatus == PaymentStatus.NotPaid, "Payment must be not confirmed");

        orders[orderId].deliveryStatus = DeliveryStatus.Cancelled;
        emit DeliveryStatusUpdated(orderId, DeliveryStatus.Cancelled);
    }

    function requestReturn(uint orderId, string memory reason) public {
        require(orderId > 0 && orderId <= orderCount, "Invalid order");
        require(orders[orderId].deliveryStatus == DeliveryStatus.DeliveredNotConfirm, "Order must be not confirmed delivered");
        require(orders[orderId].paymentStatus == PaymentStatus.NotPaid, "Payment must be not confirmed");

        orders[orderId].deliveryStatus = DeliveryStatus.ReturnRequested;
        orders[orderId].returnReason = reason;

        emit DeliveryStatusUpdated(orderId, DeliveryStatus.ReturnRequested);
        emit ReturnRequestedEvent(orderId, reason);
    }
}