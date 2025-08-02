//
//  Item.swift
//  Samay_MacOS
//
//  Created by Akshit Harsola on 27/07/25.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
