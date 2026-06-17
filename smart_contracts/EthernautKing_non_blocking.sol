// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract King {
    address king;
    uint256 public prize;
    address public owner;
    mapping(address => uint256) public withdrawable;

    constructor() payable {
        owner = msg.sender;
        king = msg.sender;
        prize = msg.value;
    }

    receive() external payable {
        require(msg.value >= prize || msg.sender == owner);
        withdrawable[king] += msg.value;
        king = msg.sender;
        prize = msg.value;
    }

    function withdraw() public {
        uint256 tmp = withdrawable[msg.sender];
        withdrawable[msg.sender] = 0;
        payable(msg.sender).transfer(tmp);
    }

    function _king() public view returns (address) {
        return king;
    }

}
