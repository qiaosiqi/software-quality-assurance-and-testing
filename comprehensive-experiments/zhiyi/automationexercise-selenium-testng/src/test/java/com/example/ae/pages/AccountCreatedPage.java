package com.example.ae.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

public class AccountCreatedPage extends BasePage {
    private final By accountCreated = By.cssSelector("[data-qa='account-created']");
    private final By continueButton = By.cssSelector("[data-qa='continue-button']");

    public AccountCreatedPage(WebDriver driver, WebDriverWait wait) {
        super(driver, wait);
    }

    public AccountCreatedPage waitUntilLoaded() {
        visible(accountCreated);
        return this;
    }

    public String getSuccessText() {
        return visible(accountCreated).getText();
    }

    public HomePage clickContinue() {
        click(continueButton);
        return new HomePage(driver, wait).waitUntilLoaded();
    }
}
