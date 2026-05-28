package com.example.ae.pages;

import com.example.ae.model.UserData;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

public class AccountInformationPage extends BasePage {
    private final By enterAccountInfoTitle = By.xpath("//*[contains(text(),'Enter Account Information')]");
    private final By titleMr = By.id("id_gender1");
    private final By password = By.cssSelector("[data-qa='password']");
    private final By days = By.cssSelector("[data-qa='days']");
    private final By months = By.cssSelector("[data-qa='months']");
    private final By years = By.cssSelector("[data-qa='years']");
    private final By newsletter = By.id("newsletter");
    private final By optin = By.id("optin");
    private final By firstName = By.cssSelector("[data-qa='first_name']");
    private final By lastName = By.cssSelector("[data-qa='last_name']");
    private final By company = By.cssSelector("[data-qa='company']");
    private final By address = By.cssSelector("[data-qa='address']");
    private final By country = By.cssSelector("[data-qa='country']");
    private final By state = By.cssSelector("[data-qa='state']");
    private final By city = By.cssSelector("[data-qa='city']");
    private final By zipcode = By.cssSelector("[data-qa='zipcode']");
    private final By mobileNumber = By.cssSelector("[data-qa='mobile_number']");
    private final By createAccountButton = By.cssSelector("[data-qa='create-account']");

    public AccountInformationPage(WebDriver driver, WebDriverWait wait) {
        super(driver, wait);
    }

    public AccountInformationPage waitUntilLoaded() {
        visible(enterAccountInfoTitle);
        return this;
    }

    public AccountCreatedPage createAccount(UserData user) {
        click(titleMr);
        type(password, user.getPassword());
        new Select(visible(days)).selectByVisibleText(user.getDay());
        new Select(visible(months)).selectByVisibleText(user.getMonth());
        new Select(visible(years)).selectByVisibleText(user.getYear());
        click(newsletter);
        click(optin);
        type(firstName, user.getFirstName());
        type(lastName, user.getLastName());
        type(company, user.getCompany());
        type(address, user.getAddress());
        new Select(visible(country)).selectByVisibleText(user.getCountry());
        type(state, user.getState());
        type(city, user.getCity());
        type(zipcode, user.getZipcode());
        type(mobileNumber, user.getMobileNumber());
        click(createAccountButton);
        return new AccountCreatedPage(driver, wait).waitUntilLoaded();
    }
}
