package com.example.lunch;

import java.util.List;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class Restaurant {
    private String name;
    private List<LunchItem> lunchMenu;
}