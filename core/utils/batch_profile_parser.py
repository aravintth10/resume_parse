from linkedin_profile_parser import extract_profile_fields

# Sample scraped bios list (replace with your real scraped results)
scraped_bios = [
    """
    Mukeshwaran s. Associate at Acuity knowledge partners. 
    Acuity Knowledge Partners SRM University. Chennai, Tamil Nadu, India. 
    856 followers 500+ connections.
    """,
    """
    Mukeshwaran P. Area Sales Manager @ One97 communications limited. 
    One97 Communications Limited karunya University. Chennai. 
    307 followers.
    """,
    """
    MUKESHWARAN D. 🛢️DB linux ‍ . Netcore Cloud KGiSL Institute of Technology. 
    Coimbatore, Tamil Nadu, India. 48 followers.
    """,
    """
    Mukeshwaran CM. Senior Test Engineer at emids. emids Alpha arts and science college. 
    Chennai, Tamil Nadu, India. 2 followers.
    """
]

def batch_process_profiles(bio_list):
    all_results = []
    for i, bio in enumerate(bio_list):
        print(f"\n🔍 Processing Profile {i+1}...")
        result = extract_profile_fields(bio)
        print(result)
        all_results.append(result)
    return all_results

if __name__ == "__main__":
    structured_results = batch_process_profiles(scraped_bios) 