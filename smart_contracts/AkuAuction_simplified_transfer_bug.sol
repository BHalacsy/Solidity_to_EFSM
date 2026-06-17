// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AkuAuction {

    address public _owner;
    address public project;

    uint256 public totalForAuction = 5495;
    uint256 public startingPrice;
    uint256 public startAt;
    uint256 public expiresAt;

    mapping(address => uint256) public bidsPlaced;
    mapping(address => uint256) public finalProcess;

    uint256 public totalBids;
    uint256 public bidIndex;
    uint256 public refundProgress;

    constructor(address _project, uint256 startingTime, uint256 _startingPrice) {
        _owner = msg.sender;
        project = _project;
        startingPrice = _startingPrice;
        startAt = startingTime;
        expiresAt = startAt + 7560;
    }

    function bid() external payable {
        require(block.timestamp > startAt);
        require(block.timestamp < expiresAt);
        require(msg.value >= startingPrice);
        require(totalBids < totalForAuction);

        uint256 existingBids = bidsPlaced[msg.sender];

        if (existingBids == 0) {
            bidIndex = bidIndex + 1;
        }

        bidsPlaced[msg.sender] = 1;
        totalBids = totalBids + 1;
    }

    function processRefund() external {
        require(block.timestamp > expiresAt);

        uint256 myFinalProcess = finalProcess[msg.sender];
        require(myFinalProcess == 0);

        uint256 myBidsPlaced = bidsPlaced[msg.sender];
        require(myBidsPlaced > 0);

        finalProcess[msg.sender] = 1;
        payable(msg.sender).transfer(startingPrice);
        refundProgress = refundProgress + 1;
    }

    function claimProjectFunds() external {
        require(msg.sender == _owner);
        require(block.timestamp > expiresAt);
        require(refundProgress >= bidIndex);

        payable(project).transfer(address(this).balance);
    }
}
