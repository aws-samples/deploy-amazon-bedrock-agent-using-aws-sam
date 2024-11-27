.PHONY: build
build:
	sam build -p

.PHONY: deploy
deploy: build
	sam deploy --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM CAPABILITY_NAMED_IAM --guided

.PHONY: update
update: build
	sam deploy --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM CAPABILITY_NAMED_IAM