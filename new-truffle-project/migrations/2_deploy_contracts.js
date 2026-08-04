const Purchase = artifacts.require("Purchase");

module.exports = function (deployer, network, accounts) {
  const vendor = accounts[0]; // or any desired vendor address
  deployer.deploy(Purchase, vendor);
};