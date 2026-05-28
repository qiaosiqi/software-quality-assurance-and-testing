package com.example.ae.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

public class AccountDeletedPage extends BasePage {
    private final By accountDeleted = By.cssSelector("[data-qa='account-deleted']");
    private final By continueButton = By.cssSelector("[data-qa='continue-button']");

    public AccountDeletedPage(WebDriver driver, WebDriverWait wait) {
        super(driver, wait);
    }

    public boolean isDeletedDisplayed() {
        return isVisible(accountDeleted);
    }

    public HomePage clickContinue() {
        click(continueButton);
        return new HomePage(driver, wait).waitUntilLoaded();
    }
}
