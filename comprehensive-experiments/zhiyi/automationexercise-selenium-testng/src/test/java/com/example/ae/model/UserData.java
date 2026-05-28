package com.example.ae.model;

/**
 * 注册用户数据模型。用 Builder 创建，方便从参数或数据文件传入。
 */
public class UserData {
    private final String name;
    private final String email;
    private final String password;
    private final String firstName;
    private final String lastName;
    private final String company;
    private final String address;
    private final String country;
    private final String state;
    private final String city;
    private final String zipcode;
    private final String mobileNumber;
    private final String day;
    private final String month;
    private final String year;

    private UserData(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.password = builder.password;
        this.firstName = builder.firstName;
        this.lastName = builder.lastName;
        this.company = builder.company;
        this.address = builder.address;
        this.country = builder.country;
        this.state = builder.state;
        this.city = builder.city;
        this.zipcode = builder.zipcode;
        this.mobileNumber = builder.mobileNumber;
        this.day = builder.day;
        this.month = builder.month;
        this.year = builder.year;
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
    public String getPassword() { return password; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getCompany() { return company; }
    public String getAddress() { return address; }
    public String getCountry() { return country; }
    public String getState() { return state; }
    public String getCity() { return city; }
    public String getZipcode() { return zipcode; }
    public String getMobileNumber() { return mobileNumber; }
    public String getDay() { return day; }
    public String getMonth() { return month; }
    public String getYear() { return year; }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String name;
        private String email;
        private String password;
        private String firstName = "Test";
        private String lastName = "User";
        private String company = "Student Lab";
        private String address = "No. 1 Software Road";
        private String country = "United States";
        private String state = "California";
        private String city = "Los Angeles";
        private String zipcode = "90001";
        private String mobileNumber = "13800000000";
        private String day = "1";
        private String month = "January";
        private String year = "2000";

        public Builder name(String name) { this.name = name; return this; }
        public Builder email(String email) { this.email = email; return this; }
        public Builder password(String password) { this.password = password; return this; }
        public Builder firstName(String firstName) { this.firstName = firstName; return this; }
        public Builder lastName(String lastName) { this.lastName = lastName; return this; }
        public Builder company(String company) { this.company = company; return this; }
        public Builder address(String address) { this.address = address; return this; }
        public Builder country(String country) { this.country = country; return this; }
        public Builder state(String state) { this.state = state; return this; }
        public Builder city(String city) { this.city = city; return this; }
        public Builder zipcode(String zipcode) { this.zipcode = zipcode; return this; }
        public Builder mobileNumber(String mobileNumber) { this.mobileNumber = mobileNumber; return this; }
        public Builder day(String day) { this.day = day; return this; }
        public Builder month(String month) { this.month = month; return this; }
        public Builder year(String year) { this.year = year; return this; }

        public UserData build() {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("name 不能为空");
            }
            if (email == null || email.isBlank()) {
                throw new IllegalArgumentException("email 不能为空");
            }
            if (password == null || password.isBlank()) {
                throw new IllegalArgumentException("password 不能为空");
            }
            return new UserData(this);
        }
    }
}
