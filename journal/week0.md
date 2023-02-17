# Week 0 — Billing and Architecture

Yipeee :dancer: :dancer: :dancer:   the Free AWS Cloud Project Bootcamp officially kicked off this week.

I hoped to send this out earlier than now but this week tried it with me.

Let's get to it, shall we!!

## HouseKeeping 

This week at the bootcamp was called week 0.
Week 0 to me was essientially housekeeping week, although there were prerequisites that needed to get done before the commencement of the bootcamp there was still a lot to put in place to ensure readiness for the project.

The housekeeping tasks I completed this week are mentioned below:

- ### Added a Virtual MFA Device to my AWS root account

Security is a very big consideration for me as I am in the cloud security space and so adding a virtual authentication device to my root account was one of the first steps I took after creating my AWS account. This is essential to provide an additional layer of protection to the account because a compromised AWS root account is the very worst thing that can happen to any organisation or even indiviual.

To do this I used the microsoft authenticator app as m virtual authenticator device.
This app and the codes were used to setup MFA, it's a pretty straight forward process and so I won't go into the details for the setup.

- ### Created a User with Admin Rights

Another security consideration is not to make use of your root account for daily use but to use it for those tasks that can be performed by only the root user. To be able to do this I created an IAM user and added the user to an admin user group I had created. 

This group was given AdministratorAccess. AdministratorAccess provides full access to AWS services and resources making the need to login to my AWS root account very little.

I also created access key for this user. This is necessary as I will use this access key to enable the AWS CLI to access my AWS account via the command line.

- ### 