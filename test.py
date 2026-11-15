import torch
import transformers



x = torch.tensor(0.5, requires_grad=True)

y = x**2

# get the gradients
y.backward()
print(x.grad)