FROM public.ecr.aws/lambda/python:3.9

# Add build tools for pip3
RUN yum install gcc -y

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

RUN mkdir /tmp/preds

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.lambda_handler" ]