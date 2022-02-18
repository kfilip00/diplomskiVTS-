-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Feb 18, 2022 at 09:29 PM
-- Server version: 10.4.22-MariaDB
-- PHP Version: 8.0.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `zavrsnirad`
--

-- --------------------------------------------------------

--
-- Table structure for table `friendrequests`
--

CREATE TABLE `friendrequests` (
  `requestId` int(11) NOT NULL,
  `sender` int(11) NOT NULL,
  `receiver` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `players`
--

CREATE TABLE `players` (
  `playerId` int(11) NOT NULL,
  `name` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(102) NOT NULL,
  `friends` varchar(255) NOT NULL DEFAULT '0' COMMENT 'id,id,id',
  `coins` int(10) NOT NULL DEFAULT 0,
  `points` int(10) NOT NULL DEFAULT 0,
  `boughtItems` varchar(200) NOT NULL DEFAULT '-' COMMENT 'id,id,id',
  `selectedHero` int(1) DEFAULT 0,
  `gamesPlayed` int(11) NOT NULL DEFAULT 0,
  `gamesWon` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `players`
--

INSERT INTO `players` (`playerId`, `name`, `email`, `password`, `friends`, `coins`, `points`, `boughtItems`, `selectedHero`, `gamesPlayed`, `gamesWon`) VALUES
(2, 'stefi', 'stefi@gmail.com', 'pbkdf2:sha256:260000$t2hJmvDfhJUBuWGS$549bfc11e8367e1816c77a3a2e636b2fcca8aa5278b7f70f0f5636808ae1a952', '0,3,4', 6809, 254, '-', 0, 2, 1),
(3, 'deki', 'deki@gmail.com', 'pbkdf2:sha256:260000$nDT0zA3LlP5SzNBG$2c177b8815ae29dd12612fd0b05b03e1df9481f1e7f971213ad91ba9176dfd0f', '0,2,7', 120, 0, '-', 0, 0, 0),
(4, 'duki', 'duki@gmail.com', 'pbkdf2:sha256:260000$O4zeVLzq7mftwhrX$cd6adf43dafa8043ffb43653dfdb7f2d9318d303e5a6d2680c7d5aa8e5a1c032', '0,2', 4107, 7, '-', 0, 2, 0),
(7, 'fiki', 'fiki@gmail.com', 'pbkdf2:sha256:260000$RpBNz1Mobte1Ctcr$90f843acf8454a6980912c5b450e8ea449443e40fd9dde82d59c73550da8cb48', '0,3', 257, 26, '-', 0, 0, 0),
(8, 'miki', 'miki@gmail.com', 'pbkdf2:sha256:260000$JulNshJBTmUZ66NQ$e5d2f46c8201b3fdcca42a22afeb74ed5dbd8f29f0f5c0386a302c9640d3b4f2', '0', 0, 0, '-', 0, 0, 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `friendrequests`
--
ALTER TABLE `friendrequests`
  ADD PRIMARY KEY (`requestId`),
  ADD KEY `friendRequest_sender` (`sender`),
  ADD KEY `friendRequest_receiver` (`receiver`);

--
-- Indexes for table `players`
--
ALTER TABLE `players`
  ADD PRIMARY KEY (`playerId`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `friendrequests`
--
ALTER TABLE `friendrequests`
  MODIFY `requestId` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `players`
--
ALTER TABLE `players`
  MODIFY `playerId` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `friendrequests`
--
ALTER TABLE `friendrequests`
  ADD CONSTRAINT `friendRequest_receiver` FOREIGN KEY (`receiver`) REFERENCES `players` (`playerId`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `friendRequest_sender` FOREIGN KEY (`sender`) REFERENCES `players` (`playerId`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
